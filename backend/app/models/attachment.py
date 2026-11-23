import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin


class Attachment(CreatedAtMixin, Base):
    """Документ, приложенный к заявке. У заявки может быть только один файл."""

    __tablename__ = "attachments"
    __table_args__ = (CheckConstraint("size_bytes > 0", name="size_positive"),)

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), unique=True
    )
    original_filename: Mapped[str] = mapped_column(String(255))
    # тип, определённый сервером по содержимому файла, а не присланный клиентом
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int]
    sha256: Mapped[str] = mapped_column(String(64))
    # случайное имя файла в хранилище, не связанное с исходным именем
    storage_key: Mapped[str] = mapped_column(String(255), unique=True)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
