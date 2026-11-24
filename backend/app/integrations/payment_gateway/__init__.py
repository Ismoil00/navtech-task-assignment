from functools import cache

from app.core.config import get_settings
from app.integrations.payment_gateway.base import ChargeResult, PaymentGateway, PaymentGatewayError
from app.integrations.payment_gateway.flaky import FlakyMockGateway
from app.integrations.payment_gateway.stable import StableMockGateway


@cache
def get_payment_gateway() -> PaymentGateway:
    """Шлюз выбирается настройкой PAYMENT_GATEWAY: flaky (по умолчанию) или stable.

    stable включает только сквозной тест, чтобы случайные отказы не роняли его.
    """
    settings = get_settings()
    if settings.payment_gateway == "stable":
        return StableMockGateway()
    return FlakyMockGateway(
        failure_rate=settings.payment_failure_rate,
        delay_rate=settings.payment_delay_rate,
        min_delay=settings.payment_delay_min_seconds,
        max_delay=settings.payment_delay_max_seconds,
    )


__all__ = [
    "ChargeResult",
    "FlakyMockGateway",
    "PaymentGateway",
    "PaymentGatewayError",
    "StableMockGateway",
    "get_payment_gateway",
]
