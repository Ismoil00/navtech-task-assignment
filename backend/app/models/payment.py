import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import PaymentStatus
from app.models.base import Base, TimestampMixin
from app.models.types import payment_status_enum


class Payment(TimestampMixin, Base):
    """Попытка оплаты заявки. Неудачные попытки сохраняются для истории."""

    __tablename__ = "payments"
    __table_args__ = (
        # Повтор запроса с тем же ключом находит уже созданный платёж
        UniqueConstraint(
            "application_id", "idempotency_key", name="uq_payments_application_idempotency_key"
        ),
        CheckConstraint("amount > 0", name="amount_positive"),
        # Последний рубеж против двойного списания: даже при ошибке в коде у заявки
        # не может быть больше одного «живого» платежа.
        Index(
            "uq_payments_one_active_per_application",
            "application_id",
            unique=True,
            postgresql_where=text("status IN ('processing', 'succeeded', 'refunded')"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="RESTRICT")
    )
    idempotency_key: Mapped[str] = mapped_column(String(64))
    amount: Mapped[int]  # в дирамах
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[PaymentStatus] = mapped_column(
        payment_status_enum,
        default=PaymentStatus.PROCESSING,
        server_default=PaymentStatus.PROCESSING.value,
    )
    provider_ref: Mapped[str | None] = mapped_column(String(100))
    failure_reason: Mapped[str | None] = mapped_column(String(255))
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
