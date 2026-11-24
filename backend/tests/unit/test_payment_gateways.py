"""Unit-тесты заглушек платёжного шлюза.

Требование ТЗ: настоящий шлюз не нужен, заглушка внутри сервиса иногда
отвечает с задержкой, а иногда ошибкой.
"""

import random
import uuid

from app.integrations.payment_gateway import (
    FlakyMockGateway,
    PaymentGatewayError,
    StableMockGateway,
)

MIN_DELAY, MAX_DELAY, LONG_DELAY = 0.3, 4.0, 10.0


class RecordingSleep:
    """Подменяет asyncio.sleep: запоминает задержки и не ждёт по-настоящему."""

    def __init__(self) -> None:
        self.delays: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.delays.append(seconds)


def make_flaky(sleep: RecordingSleep, failure_rate: float = 0.2) -> FlakyMockGateway:
    return FlakyMockGateway(
        failure_rate=failure_rate,
        min_delay=MIN_DELAY,
        max_delay=MAX_DELAY,
        long_delay_rate=0.1,
        long_delay=LONG_DELAY,
        rng=random.Random(42),  # фиксированный seed — результат воспроизводим
        sleep=sleep,
    )


async def charge_many(gateway: FlakyMockGateway | StableMockGateway, count: int) -> list[str]:
    outcomes = []
    for _ in range(count):
        try:
            await gateway.charge(uuid.uuid4(), 5000, "TJS")
            outcomes.append("ok")
        except PaymentGatewayError as error:
            assert error.reason  # у отказа всегда есть причина для пользователя
            outcomes.append("error")
    return outcomes


async def test_flaky_gateway_sometimes_fails() -> None:
    outcomes = await charge_many(make_flaky(RecordingSleep()), 200)

    assert "ok" in outcomes
    assert "error" in outcomes
    assert 0.1 < outcomes.count("error") / len(outcomes) < 0.3


async def test_flaky_gateway_always_answers_with_delay() -> None:
    sleep = RecordingSleep()
    await charge_many(make_flaky(sleep), 200)

    assert len(sleep.delays) == 200
    regular = [delay for delay in sleep.delays if delay != LONG_DELAY]
    assert all(MIN_DELAY <= delay <= MAX_DELAY for delay in regular)
    # часть ответов приходит дольше, чем ждёт фронтенд
    assert LONG_DELAY in sleep.delays


async def test_failure_rate_controls_errors() -> None:
    assert set(await charge_many(make_flaky(RecordingSleep(), failure_rate=0), 50)) == {"ok"}
    assert set(await charge_many(make_flaky(RecordingSleep(), failure_rate=1), 50)) == {"error"}


async def test_stable_gateway_always_succeeds() -> None:
    assert set(await charge_many(StableMockGateway(), 50)) == {"ok"}
