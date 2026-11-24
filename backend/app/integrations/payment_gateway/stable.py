import uuid

from app.integrations.payment_gateway.base import ChargeResult


class StableMockGateway:
    """Заглушка без сбоев: списание проходит сразу. Для демонстрации и E2E-тестов."""

    async def charge(self, payment_id: uuid.UUID, amount: int, currency: str) -> ChargeResult:
        return ChargeResult(provider_ref=f"stable-{payment_id.hex[:12]}")

    async def refund(self, payment_id: uuid.UUID, provider_ref: str) -> None:
        return None
