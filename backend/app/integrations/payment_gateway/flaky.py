import asyncio
import enum
import random
import uuid
from collections.abc import Awaitable, Callable

from app.integrations.payment_gateway.base import ChargeResult, PaymentGatewayError

_FAILURE_REASONS = (
    "Банк-эмитент отклонил операцию",
    "Платёжный шлюз временно недоступен",
    "Недостаточно средств на карте",
)

# обычное время ответа шлюза (успех или отказ), секунды
_REGULAR_LATENCY = (0.3, 1.0)


class Outcome(enum.Enum):
    SUCCESS = "success"
    DELAY = "delay"  # успешный ответ, но с долгой задержкой
    FAILURE = "failure"


class FlakyMockGateway:
    """Заглушка нестабильного шлюза: часть оплат отвечает с задержкой, часть — ошибкой.

    Исходы выдаются сериями по 10 оплат. В каждой серии ровно столько отказов и задержек,
    сколько задано долями в .env (по умолчанию 3 отказа, 3 задержки, 4 быстрых успеха),
    порядок внутри серии случайный. Так доли соблюдаются и на коротком ручном прогоне,
    а не только «в среднем на тысяче оплат».
    """

    SERIES_SIZE = 10

    def __init__(
        self,
        *,
        failure_rate: float,
        delay_rate: float,
        min_delay: float,
        max_delay: float,
        rng: random.Random | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        failures = round(failure_rate * self.SERIES_SIZE)
        delays = round(delay_rate * self.SERIES_SIZE)
        successes = self.SERIES_SIZE - failures - delays
        if failures < 0 or delays < 0 or successes < 0:
            raise ValueError("Доли отказов и задержек должны быть от 0 до 1 и в сумме не больше 1")
        self._series = (
            [Outcome.FAILURE] * failures + [Outcome.DELAY] * delays + [Outcome.SUCCESS] * successes
        )
        self._pending: list[Outcome] = []
        self._min_delay = min_delay
        self._max_delay = max_delay
        # генератор и sleep подставляются в тестах, чтобы поведение было воспроизводимым
        self._rng = rng or random.Random()
        self._sleep = sleep

    async def charge(self, payment_id: uuid.UUID, amount: int, currency: str) -> ChargeResult:
        outcome = self.next_outcome()
        if outcome is Outcome.DELAY:
            await self._sleep(self._rng.uniform(self._min_delay, self._max_delay))
        else:
            await self._sleep(self._rng.uniform(*_REGULAR_LATENCY))
        if outcome is Outcome.FAILURE:
            raise PaymentGatewayError(self._rng.choice(_FAILURE_REASONS))
        return ChargeResult(provider_ref=f"mock-{uuid.uuid4().hex[:16]}")

    async def refund(self, payment_id: uuid.UUID, provider_ref: str) -> None:
        # сбои имитируются только при списании; возврат выполняется сразу
        return None

    def next_outcome(self) -> Outcome:
        if not self._pending:
            self._pending = self._series.copy()
            self._rng.shuffle(self._pending)
        return self._pending.pop()
