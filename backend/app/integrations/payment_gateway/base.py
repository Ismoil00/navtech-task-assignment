import uuid
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ChargeResult:
    provider_ref: str  # номер операции на стороне платёжного провайдера


class PaymentGatewayError(Exception):
    """Шлюз отказал в списании или не смог его выполнить. Деньги не списаны."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class PaymentGateway(Protocol):
    """Платёжный шлюз. Реального провайдера нет — используются две заглушки.

    payment_id передаётся как ключ идемпотентности провайдера: так работают
    реальные шлюзы, и повтор запроса с тем же id не приводит к второму списанию.
    """

    async def charge(self, payment_id: uuid.UUID, amount: int, currency: str) -> ChargeResult:
        """Списывает сумму (в минимальных единицах валюты) или бросает PaymentGatewayError."""

    async def refund(self, payment_id: uuid.UUID, provider_ref: str) -> None:
        """Возвращает ранее списанные деньги."""
