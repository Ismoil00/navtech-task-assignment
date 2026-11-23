import uuid

from sqlalchemy import BigInteger, ForeignKey, Identity, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import ApplicationStatus
from app.models.base import Base, CreatedAtMixin
from app.models.types import application_status_enum
from app.models.user import User


class ApplicationStatusHistory(CreatedAtMixin, Base):
    """Журнал смены статусов: кто, когда и с каким комментарием."""

    __tablename__ = "application_status_history"
    __table_args__ = (
        Index("ix_application_status_history_application", "application_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE")
    )
    # None у первой записи — создание заявки
    from_status: Mapped[ApplicationStatus | None] = mapped_column(application_status_enum)
    to_status: Mapped[ApplicationStatus] = mapped_column(application_status_enum)
    actor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    comment: Mapped[str | None] = mapped_column(String(1000))

    actor: Mapped[User] = relationship(lazy="raise")
