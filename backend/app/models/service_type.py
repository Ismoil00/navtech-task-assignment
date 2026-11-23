from sqlalchemy import CheckConstraint, Identity, SmallInteger, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ServiceType(Base):
    """Справочник услуг. Цена хранится в дирамах (1 сомони = 100 дирам)."""

    __tablename__ = "service_types"
    __table_args__ = (CheckConstraint("price > 0", name="price_positive"),)

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(String(500))
    price: Mapped[int]
    currency: Mapped[str] = mapped_column(String(3), default="TJS", server_default="TJS")
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")
