"""Оплата заявки.

Как исключено двойное списание (двойной клик, повтор после таймаута):
1. Фронтенд создаёт Idempotency-Key на попытку оплаты и повторяет запрос с ним же.
   Запрос с уже известным ключом возвращает тот же платёж, шлюз не вызывается.
2. Строка заявки блокируется (SELECT ... FOR UPDATE): одновременные запросы
   по одной заявке проверяются строго по очереди.
3. Если у заявки уже есть успешный платёж — он и возвращается; если платёж ещё
   обрабатывается — новый запрос получает 409 PAYMENT_IN_PROGRESS.
4. В БД частичный уникальный индекс: больше одного «живого» платежа на заявку
   не сохранить, даже если в коде окажется ошибка.

Шлюз вызывается вне транзакции (он может отвечать секундами) и под
asyncio.shield: если клиент оборвёт соединение, результат всё равно запишется.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.core.errors import AppError, NotFoundError
from app.domain.enums import AllowedAction, ApplicationAction, PaymentStatus
from app.domain.status_machine import get_transition
from app.integrations.payment_gateway import PaymentGateway, PaymentGatewayError
from app.models import Application, Payment, User
from app.repositories.application_repository import ApplicationRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.service_type_repository import ServiceTypeRepository
from app.repositories.user_repository import UserRepository
from app.services import allowed_actions
from app.services.application_workflow import ApplicationWorkflow, PaymentInProgressError

logger = logging.getLogger(__name__)


class PaymentFailedError(AppError):
    status_code = 502
    code = "PAYMENT_FAILED"
    message = "Оплата не прошла. Попробуйте ещё раз"


@dataclass(frozen=True)
class PaymentOutcome:
    payment: Payment
    application: Application
    allowed_actions: list[AllowedAction]


class PaymentService:
    def __init__(
        self,
        session: AsyncSession,
        session_factory: async_sessionmaker[AsyncSession],
        gateway: PaymentGateway,
    ) -> None:
        self._session = session
        self._session_factory = session_factory
        self._gateway = gateway
        self._applications = ApplicationRepository(session)
        self._payments = PaymentRepository(session)
        self._service_types = ServiceTypeRepository(session)
        self._workflow = ApplicationWorkflow(session)

    async def pay(
        self, applicant: User, application_id: uuid.UUID, idempotency_key: str
    ) -> PaymentOutcome:
        payment_id, is_new = await self._start(applicant, application_id, idempotency_key)
        if is_new:
            await asyncio.shield(self._complete(payment_id, applicant.id))
        return await self._outcome(payment_id, application_id)

    async def _start(
        self, applicant: User, application_id: uuid.UUID, idempotency_key: str
    ) -> tuple[uuid.UUID, bool]:
        """Транзакция 1: решить, нужно ли списание, и зарезервировать платёж."""
        try:
            application = await self._applications.get_own(
                application_id, applicant.id, for_update=True
            )
            if application is None:
                raise NotFoundError("Заявка не найдена", code="APPLICATION_NOT_FOUND")

            # тот же запрос пришёл повторно: двойной клик или повтор после таймаута
            same_request = await self._payments.get_by_key(application.id, idempotency_key)
            if same_request is not None:
                return same_request.id, False

            active = await self._payments.get_active(application.id)
            if active is not None:
                if active.status == PaymentStatus.PROCESSING:
                    raise PaymentInProgressError()
                return active.id, False  # уже оплачено — второй раз не списываем

            await self._workflow.check_requirements(application, ApplicationAction.PAY)
            get_transition(application.status, ApplicationAction.PAY, applicant.role)

            service_type = await self._service_types.get(application.service_type_id)
            if service_type is None:
                raise NotFoundError("Услуга не найдена", code="SERVICE_TYPE_NOT_FOUND")
            payment = Payment(
                application_id=application.id,
                idempotency_key=idempotency_key,
                amount=service_type.price,
                currency=service_type.currency,
                status=PaymentStatus.PROCESSING,
            )
            self._payments.add(payment)
            await self._session.commit()
            return payment.id, True
        except IntegrityError as exc:
            # сработал уникальный индекс: другой запрос успел создать платёж
            raise PaymentInProgressError() from exc
        finally:
            # снимаем блокировку строки, если транзакция не была закоммичена
            if self._session.in_transaction():
                await self._session.rollback()

    async def _complete(self, payment_id: uuid.UUID, applicant_id: uuid.UUID) -> None:
        """Вызов шлюза и транзакция 2 — в своей сессии, независимой от запроса."""
        async with self._session_factory() as session:
            payments = PaymentRepository(session)
            payment = await payments.get(payment_id)
            if payment is None:
                return

            try:
                charge = await asyncio.wait_for(
                    self._gateway.charge(payment.id, payment.amount, payment.currency),
                    timeout=get_settings().payment_gateway_timeout_seconds,
                )
            except PaymentGatewayError as exc:
                await self._mark_failed(session, payment, exc.reason)
                return
            except TimeoutError:
                await self._mark_failed(session, payment, "Платёжный шлюз не ответил вовремя")
                return
            except Exception:
                logger.exception("Сбой при обращении к платёжному шлюзу")
                await self._mark_failed(session, payment, "Ошибка при обращении к платёжному шлюзу")
                return

            application = await ApplicationRepository(session).get_by_id(
                payment.application_id, for_update=True
            )
            actor = await UserRepository(session).get_by_id(applicant_id)
            if application is None or actor is None:
                return
            payment.status = PaymentStatus.SUCCEEDED
            payment.provider_ref = charge.provider_ref
            # draft -> paid; пока платёж в обработке, заявку нельзя менять, так что она в draft
            await ApplicationWorkflow(session).apply(application, ApplicationAction.PAY, actor)
            await session.commit()

    @staticmethod
    async def _mark_failed(session: AsyncSession, payment: Payment, reason: str) -> None:
        payment.status = PaymentStatus.FAILED
        payment.failure_reason = reason
        await session.commit()

    async def _outcome(self, payment_id: uuid.UUID, application_id: uuid.UUID) -> PaymentOutcome:
        payment = await self._payments.get(payment_id)
        application = await self._applications.get_details(application_id)
        if payment is None or application is None:
            raise NotFoundError("Заявка не найдена", code="APPLICATION_NOT_FOUND")
        if payment.status == PaymentStatus.FAILED:
            raise PaymentFailedError(
                f"Оплата не прошла: {payment.failure_reason}. Попробуйте ещё раз",
                details={"payment_id": str(payment.id)},
            )
        return PaymentOutcome(
            payment=payment,
            application=application,
            allowed_actions=allowed_actions.for_applicant(application),
        )
