"""Интеграционные тесты оплаты: API + настоящий PostgreSQL + управляемый шлюз.

Требования ТЗ:
- оплата — заглушка, которая может ответить ошибкой;
- повторный запрос на оплату той же заявки (двойной клик, повтор после
  таймаута) не должен приводить ко второму списанию;
- без оплаты отправить нельзя.
"""

import asyncio
import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.db import SessionFactory
from app.domain.enums import PaymentStatus
from app.models import Payment
from tests.integration.api import Actor, Api, payments_of
from tests.integration.conftest import FakeGateway, wait_until


async def test_successful_payment_moves_draft_to_paid(
    api: Api, applicant: Actor, gateway: FakeGateway
) -> None:
    application_id = await api.draft_with_file(applicant, service_type_id=3)

    response = await api.pay(applicant, application_id)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "paid"
    assert body["payment"]["status"] == "succeeded"
    assert body["payment"]["amount"] == 12000  # цена услуги из справочника, в дирамах
    assert body["allowed_actions"] == ["submit"]
    assert [(h["from_status"], h["to_status"]) for h in body["history"]][-1] == ("draft", "paid")
    assert len(gateway.charges) == 1


async def test_same_key_twice_charges_once(
    api: Api, applicant: Actor, gateway: FakeGateway
) -> None:
    application_id = await api.draft_with_file(applicant)
    key = uuid.uuid4().hex

    first = await api.pay(applicant, application_id, key)
    second = await api.pay(applicant, application_id, key)

    assert first.status_code == second.status_code == 200
    assert first.json()["payment"]["id"] == second.json()["payment"]["id"]
    assert len(gateway.charges) == 1
    assert len(await payments_of(application_id)) == 1


async def test_double_click_while_gateway_is_slow(
    api: Api, applicant: Actor, gateway: FakeGateway
) -> None:
    application_id = await api.draft_with_file(applicant)
    key = uuid.uuid4().hex
    release = gateway.hold()

    first = asyncio.create_task(api.pay(applicant, application_id, key))
    await wait_until(lambda: len(gateway.charges) == 1)
    # второй клик, пока шлюз ещё думает: ответ сразу, без нового списания
    second = await api.pay(applicant, application_id, key)
    assert second.status_code == 202
    assert second.json()["payment"]["status"] == "processing"
    assert second.json()["allowed_actions"] == []

    release.set()
    assert (await first).status_code == 200
    assert len(gateway.charges) == 1
    assert [p.status for p in await payments_of(application_id)] == [PaymentStatus.SUCCEEDED]


async def test_retry_after_client_timeout_does_not_charge_twice(
    api: Api, applicant: Actor, gateway: FakeGateway
) -> None:
    application_id = await api.draft_with_file(applicant)
    key = uuid.uuid4().hex
    release = gateway.hold()

    # клиент не дождался ответа и оборвал запрос
    first = asyncio.create_task(api.pay(applicant, application_id, key))
    await wait_until(lambda: len(gateway.charges) == 1)
    first.cancel()
    release.set()

    # сервер всё равно довёл оплату до конца и записал результат
    async def payment_finished() -> bool:
        payments = await payments_of(application_id)
        return payments[0].status != PaymentStatus.PROCESSING

    await wait_until(payment_finished)

    # повтор с тем же ключом получает готовый результат
    retry = await api.pay(applicant, application_id, key)
    assert retry.status_code == 200
    assert retry.json()["status"] == "paid"
    assert len(gateway.charges) == 1


async def test_another_attempt_while_payment_in_progress_is_rejected(
    api: Api, applicant: Actor, gateway: FakeGateway
) -> None:
    application_id = await api.draft_with_file(applicant)
    release = gateway.hold()

    first = asyncio.create_task(api.pay(applicant, application_id))
    await wait_until(lambda: len(gateway.charges) == 1)
    second = await api.pay(applicant, application_id)  # другой ключ

    assert second.status_code == 409
    assert second.json()["error"]["code"] == "PAYMENT_IN_PROGRESS"
    release.set()
    assert (await first).status_code == 200
    assert len(gateway.charges) == 1


async def test_paid_application_is_not_charged_again(
    api: Api, applicant: Actor, gateway: FakeGateway
) -> None:
    application_id = await api.paid_application(applicant)

    response = await api.pay(applicant, application_id)  # новый ключ

    assert response.status_code == 200
    assert response.json()["payment"]["status"] == "succeeded"
    assert len(gateway.charges) == 1
    assert len(await payments_of(application_id)) == 1


async def test_gateway_error_keeps_draft_and_allows_retry(
    api: Api, applicant: Actor, gateway: FakeGateway
) -> None:
    application_id = await api.draft_with_file(applicant)
    gateway.fail_with = "Банк-эмитент отклонил операцию"

    failed = await api.pay(applicant, application_id)

    assert failed.status_code == 502
    assert failed.json()["error"]["code"] == "PAYMENT_FAILED"
    assert "Банк-эмитент отклонил операцию" in failed.json()["error"]["message"]
    after_failure = (await api.get(applicant, application_id)).json()
    assert after_failure["status"] == "draft"
    assert "pay" in after_failure["allowed_actions"]

    gateway.fail_with = None
    retried = await api.pay(applicant, application_id)  # новая попытка — новый ключ

    assert retried.status_code == 200
    assert retried.json()["status"] == "paid"
    statuses = [p.status for p in await payments_of(application_id)]
    assert statuses == [PaymentStatus.FAILED, PaymentStatus.SUCCEEDED]


async def test_replaying_failed_key_does_not_charge_again(
    api: Api, applicant: Actor, gateway: FakeGateway
) -> None:
    application_id = await api.draft_with_file(applicant)
    gateway.fail_with = "Платёжный шлюз временно недоступен"
    key = uuid.uuid4().hex

    await api.pay(applicant, application_id, key)
    replay = await api.pay(applicant, application_id, key)

    assert replay.status_code == 502
    assert len(gateway.charges) == 1


async def test_payment_requires_document(api: Api, applicant: Actor, gateway: FakeGateway) -> None:
    application = await api.create_application(applicant)

    response = await api.pay(applicant, application["id"])

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "FILE_REQUIRED"
    assert gateway.charges == []


async def test_submit_requires_payment(api: Api, applicant: Actor) -> None:
    application_id = await api.draft_with_file(applicant)

    response = await api.submit(applicant, application_id)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PAYMENT_REQUIRED"


async def test_database_rejects_second_live_payment(api: Api, applicant: Actor) -> None:
    """Последний рубеж: даже в обход сервиса в БД не сохранить второй успешный платёж."""
    application_id = uuid.UUID(await api.paid_application(applicant))

    async with SessionFactory() as session:
        session.add(
            Payment(
                application_id=application_id,
                idempotency_key="bypass-service",
                amount=5000,
                currency="TJS",
                status=PaymentStatus.SUCCEEDED,
            )
        )
        with pytest.raises(IntegrityError):
            await session.commit()
