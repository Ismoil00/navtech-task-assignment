import uuid

from sqlalchemy import String, text, true
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import UserRole
from app.models.base import Base, CreatedAtMixin
from app.models.types import user_role_enum


class User(CreatedAtMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(150))
    role: Mapped[UserRole] = mapped_column(user_role_enum)
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())
