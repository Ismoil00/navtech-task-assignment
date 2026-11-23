import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import ApplicationStatus
from app.models.base import Base, TimestampMixin
from app.models.service_type import ServiceType
from app.models.types import application_status_enum
from app.models.user import User


class Application(TimestampMixin, Base):
    __tablename__ = "applications"
    __table_args__ = (
        # список заявок заявителя
        Index("ix_applications_applicant_created", "applicant_id", "created_at"),
        # очередь оператора: фильтр по статусу и услуге, сортировка по дате отправки
        Index("ix_applications_queue", "status", "service_type_id", "submitted_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    applicant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    service_type_id: Mapped[int] = mapped_column(
        ForeignKey("service_types.id", ondelete="RESTRICT")
    )
    full_name: Mapped[str] = mapped_column(String(150))
    phone: Mapped[str] = mapped_column(String(20))
    comment: Mapped[str | None] = mapped_column(String(1000))
    status: Mapped[ApplicationStatus] = mapped_column(
        application_status_enum,
        default=ApplicationStatus.DRAFT,
        server_default=ApplicationStatus.DRAFT.value,
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # мягкое удаление черновика: история неудачных попыток оплаты сохраняется
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # lazy="raise": в async-коде связи грузим только явно (selectinload/joinedload)
    applicant: Mapped[User] = relationship(lazy="raise")
    service_type: Mapped[ServiceType] = relationship(lazy="raise")
