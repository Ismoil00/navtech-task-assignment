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
