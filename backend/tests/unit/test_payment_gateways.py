"""Unit-тесты заглушек платёжного шлюза.

Что проверяется: нестабильная заглушка в каждой серии из 10 оплат даёт ровно
3 отказа, 3 ответа с задержкой и 4 быстрых успеха в случайном порядке, у отказа
всегда есть причина; стабильная всегда успешна.
"""

import random
import uuid

import pytest

from app.integrations.payment_gateway import (
    FlakyMockGateway,
    PaymentGatewayError,
    StableMockGateway,
)

MIN_DELAY, MAX_DELAY = 5.0, 12.0


class RecordingSleep:
    """Подменяет asyncio.sleep: запоминает задержки и не ждёт по-настоящему."""

    def __init__(self) -> None:
        self.delays: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.delays.append(seconds)


def make_flaky(
    sleep: RecordingSleep, failure_rate: float = 0.3, delay_rate: float = 0.3, seed: int = 42
) -> FlakyMockGateway:
    return FlakyMockGateway(
        failure_rate=failure_rate,
        delay_rate=delay_rate,
        min_delay=MIN_DELAY,
        max_delay=MAX_DELAY,
        rng=random.Random(seed),  # фиксированный seed — результат воспроизводим
        sleep=sleep,
    )


async def charge_many(gateway: FlakyMockGateway | StableMockGateway, count: int) -> list[str]:
    """Исход каждой оплаты: error, delay (успех после долгой задержки) или ok."""
    sleep = getattr(gateway, "_sleep", None)
    outcomes = []
    for _ in range(count):
        try:
            await gateway.charge(uuid.uuid4(), 5000, "TJS")
            delayed = isinstance(sleep, RecordingSleep) and sleep.delays[-1] >= MIN_DELAY
            outcomes.append("delay" if delayed else "ok")
        except PaymentGatewayError as error:
            assert error.reason  # у отказа всегда есть причина для пользователя
            outcomes.append("error")
    return outcomes


async def test_every_series_of_ten_has_exact_split() -> None:
    outcomes = await charge_many(make_flaky(RecordingSleep()), 100)

    for start in range(0, 100, 10):
        series = outcomes[start : start + 10]
        assert (series.count("error"), series.count("delay"), series.count("ok")) == (3, 3, 4)


async def test_order_inside_series_is_random() -> None:
    first = await charge_many(make_flaky(RecordingSleep(), seed=1), 10)
    second = await charge_many(make_flaky(RecordingSleep(), seed=2), 10)

    assert sorted(first) == sorted(second)
    assert first != second


async def test_delays_are_long_and_other_answers_are_quick() -> None:
    sleep = RecordingSleep()
    outcomes = await charge_many(make_flaky(sleep), 50)

    for outcome, delay in zip(outcomes, sleep.delays, strict=True):
        if outcome == "delay":
            assert MIN_DELAY <= delay <= MAX_DELAY
        else:
            assert delay < MIN_DELAY


async def test_rates_are_configurable() -> None:
    no_failures = await charge_many(make_flaky(RecordingSleep(), failure_rate=0), 20)
    only_failures = await charge_many(
        make_flaky(RecordingSleep(), failure_rate=1, delay_rate=0), 20
    )

    assert "error" not in no_failures
    assert set(only_failures) == {"error"}


def test_rates_over_one_are_rejected() -> None:
    with pytest.raises(ValueError):
        make_flaky(RecordingSleep(), failure_rate=0.7, delay_rate=0.5)


async def test_stable_gateway_always_succeeds() -> None:
    assert set(await charge_many(StableMockGateway(), 50)) == {"ok"}
