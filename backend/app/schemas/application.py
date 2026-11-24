import uuid
from datetime import datetime
from typing import Annotated, Self

import phonenumbers
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, field_validator

from app.core.config import get_settings
from app.domain.enums import AllowedAction, ApplicationStatus, PaymentStatus, UserRole
from app.models import Application, Payment

# --- Валидация полей заявки (те же правила повторяет фронтенд) ---

_NAME_PUNCTUATION = frozenset(" -'’ʼ.")


def _normalize_full_name(value: str) -> str:
    value = " ".join(value.split())
    if not 3 <= len(value) <= 150:
        raise ValueError("ФИО должно содержать от 3 до 150 символов")
    # isalpha() принимает буквы любого алфавита, в том числе таджикские ғ ӣ қ ӯ ҳ ҷ
    if any(not (char.isalpha() or char in _NAME_PUNCTUATION) for char in value):
        raise ValueError("ФИО может содержать только буквы, пробел, дефис, апостроф и точку")
    words = [word for word in value.split(" ") if any(char.isalpha() for char in word)]
    if len(words) < 2:
        raise ValueError("Укажите как минимум фамилию и имя")
    return value


def _normalize_phone(value: str) -> str:
    try:
        number = phonenumbers.parse(value, get_settings().phone_default_region)
    except phonenumbers.NumberParseException as exc:
        raise ValueError("Некорректный номер телефона") from exc
    if not phonenumbers.is_valid_number(number):
        raise ValueError("Некорректный номер телефона")
    # храним в едином формате E.164: +992931234567
    return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)


def _normalize_comment(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip() or None


FullName = Annotated[str, Field(max_length=200), AfterValidator(_normalize_full_name)]
Phone = Annotated[str, Field(max_length=30), AfterValidator(_normalize_phone)]
Comment = Annotated[str | None, Field(max_length=1000), AfterValidator(_normalize_comment)]
ServiceTypeId = Annotated[int, Field(gt=0)]


class ApplicationCreate(BaseModel):
    # неизвестные поля отклоняются: статус или владельца через API не подменить
    model_config = ConfigDict(extra="forbid")

    full_name: FullName
    phone: Phone
    service_type_id: ServiceTypeId
    comment: Comment = None


class ApplicationUpdate(BaseModel):
    """Частичное изменение: меняются только переданные поля."""

    model_config = ConfigDict(extra="forbid")

    full_name: FullName | None = None
    phone: Phone | None = None
    service_type_id: ServiceTypeId | None = None
    comment: Comment = None

    @field_validator("full_name", "phone", "service_type_id", mode="before")
    @classmethod
    def _required_if_present(cls, value: object) -> object:
        if value is None:
            raise ValueError("Обязательное поле")
        return value


# --- Ответы ---


class ServiceTypeBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: int
    currency: str


class AttachmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    content_type: str
    size_bytes: int
    created_at: datetime


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: PaymentStatus
    amount: int  # в дирамах
    currency: str
    failure_reason: str | None
    created_at: datetime
    updated_at: datetime
    refunded_at: datetime | None


def _current_payment(payments: list[Payment]) -> Payment | None:
    """Платёж для показа: «живой» (в обработке, успешный, возвращённый), иначе последний."""
    active = [payment for payment in payments if payment.status != PaymentStatus.FAILED]
    if active:
        return active[-1]
    return payments[-1] if payments else None


class HistoryActor(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    full_name: str
    role: UserRole


class StatusHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    from_status: ApplicationStatus | None
    to_status: ApplicationStatus
    comment: str | None
    created_at: datetime
    actor: HistoryActor


class ApplicationListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: ApplicationStatus
    service_type: ServiceTypeBrief
    full_name: str
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None


class ApplicationRead(ApplicationListItem):
    phone: str
    comment: str | None
    decided_at: datetime | None
    attachment: AttachmentRead | None
    payment: PaymentRead | None = None
    history: list[StatusHistoryRead]
    allowed_actions: list[AllowedAction] = []

    @classmethod
    def build(cls, application: Application, allowed_actions: list[AllowedAction]) -> Self:
        result = cls.model_validate(application)
        payment = _current_payment(application.payments)
        result.payment = PaymentRead.model_validate(payment) if payment else None
        result.allowed_actions = allowed_actions
        return result
