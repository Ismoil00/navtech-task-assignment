from enum import StrEnum


class UserRole(StrEnum):
    APPLICANT = "applicant"
    OPERATOR = "operator"


class ApplicationStatus(StrEnum):
    DRAFT = "draft"  # черновик: можно править, прикреплять файл, оплачивать
    PAID = "paid"  # оплачена, ждёт отправки заявителем
    SUBMITTED = "submitted"  # отправлена, на рассмотрении у оператора
    APPROVED = "approved"  # одобрена (финальный статус)
    REJECTED = "rejected"  # отклонена, деньги возвращены (финальный статус)
    RETURNED = "returned"  # возвращена на доработку, повторная оплата не нужна


class ApplicationAction(StrEnum):
    """Действия, меняющие статус заявки."""

    PAY = "pay"
    SUBMIT = "submit"
    APPROVE = "approve"
    REJECT = "reject"
    RETURN = "return"


class AllowedAction(StrEnum):
    """Что пользователь может сделать с заявкой прямо сейчас.

    Сервер отдаёт этот список вместе с заявкой, а интерфейс показывает только
    соответствующие кнопки — правила не дублируются на фронтенде.
    """

    EDIT = "edit"
    UPLOAD_FILE = "upload_file"
    DELETE = "delete"
    PAY = "pay"
    SUBMIT = "submit"
    APPROVE = "approve"
    REJECT = "reject"
    RETURN = "return"


class PaymentStatus(StrEnum):
    PROCESSING = "processing"  # запрос в шлюз отправлен, ответа ещё нет
    SUCCEEDED = "succeeded"
    FAILED = "failed"  # можно повторить новой попыткой
    REFUNDED = "refunded"  # деньги возвращены при отклонении заявки
