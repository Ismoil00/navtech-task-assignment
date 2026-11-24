import asyncio
import random
import uuid
from collections.abc import Awaitable, Callable

from app.integrations.payment_gateway.base import ChargeResult, PaymentGatewayError

_FAILURE_REASONS = (
    "Банк-эмитент отклонил операцию",
    "Платёжный шлюз временно недоступен",
    "Недостаточно средств на карте",
)


class FlakyMockGateway:
    """Заглушка, которая ведёт себя как настоящий нестабильный шлюз (требование ТЗ).

    Каждое списание отвечает с задержкой. Часть запросов отвечает очень долго —
    дольше, чем ждёт фронтенд, чтобы проверить сценарий «повтор после таймаута».
    Часть запросов завершается ошибкой. Все вероятности задаются в .env.
    """

    def __init__(
        self,
        *,
        failure_rate: float,
        min_delay: float,
        max_delay: float,
        long_delay_rate: float,
        long_delay: float,
        rng: random.Random | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._failure_rate = failure_rate
        self._min_delay = min_delay
        self._max_delay = max_delay
        self._long_delay_rate = long_delay_rate
        self._long_delay = long_delay
        # генератор и sleep подставляются в тестах, чтобы поведение было воспроизводимым
        self._rng = rng or random.Random()
        self._sleep = sleep

    async def charge(self, payment_id: uuid.UUID, amount: int, currency: str) -> ChargeResult:
        await self._sleep(self._next_delay())
        if self._rng.random() < self._failure_rate:
            raise PaymentGatewayError(self._rng.choice(_FAILURE_REASONS))
        return ChargeResult(provider_ref=f"mock-{uuid.uuid4().hex[:16]}")

    async def refund(self, payment_id: uuid.UUID, provider_ref: str) -> None:
        # по ТЗ нестабильной должна быть оплата; возврат выполняется сразу
        return None

    def _next_delay(self) -> float:
        if self._rng.random() < self._long_delay_rate:
            return self._long_delay
        return self._rng.uniform(self._min_delay, self._max_delay)
