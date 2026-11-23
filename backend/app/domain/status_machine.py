"""Машина состояний заявки — единственный источник правил смены статуса.

Модуль ничего не знает о БД и HTTP: по статусу, действию и роли он либо
возвращает переход, либо объясняет, почему переход невозможен. Проверки,
которым нужны данные из БД (приложен ли файл, есть ли оплата), выполняет
сервисный слой.

    draft ──pay──> paid ──submit──> submitted ──approve──> approved
                                     │  ▲   └──reject───> rejected
                                     │  │
                              return │  │ submit (без повторной оплаты)
                                     ▼  │
                                   returned
"""

from dataclasses import dataclass

from app.core.errors import BusinessValidationError, ConflictError, ForbiddenError
from app.domain.enums import ApplicationAction, ApplicationStatus, UserRole

Status = ApplicationStatus
Action = ApplicationAction


@dataclass(frozen=True)
class Transition:
    source: ApplicationStatus
    action: ApplicationAction
    target: ApplicationStatus
    role: UserRole
    comment_required: bool = False


TRANSITIONS: tuple[Transition, ...] = (
    # статус меняется на paid только после успешного ответа платёжного шлюза
    Transition(Status.DRAFT, Action.PAY, Status.PAID, UserRole.APPLICANT),
    Transition(Status.PAID, Action.SUBMIT, Status.SUBMITTED, UserRole.APPLICANT),
    Transition(Status.RETURNED, Action.SUBMIT, Status.SUBMITTED, UserRole.APPLICANT),
    Transition(Status.SUBMITTED, Action.APPROVE, Status.APPROVED, UserRole.OPERATOR),
    Transition(
        Status.SUBMITTED, Action.REJECT, Status.REJECTED, UserRole.OPERATOR, comment_required=True
    ),
    Transition(
        Status.SUBMITTED, Action.RETURN, Status.RETURNED, UserRole.OPERATOR, comment_required=True
    ),
)

_TRANSITIONS_BY_KEY = {(t.source, t.action): t for t in TRANSITIONS}
_ACTIONS_BY_ROLE = {
    role: frozenset(t.action for t in TRANSITIONS if t.role == role) for role in UserRole
}

# Править поля и файл можно только в черновике и после возврата на доработку
EDITABLE_STATUSES = frozenset({Status.DRAFT, Status.RETURNED})
# Удалить можно только неоплаченный черновик
DELETABLE_STATUSES = frozenset({Status.DRAFT})
TERMINAL_STATUSES = frozenset({Status.APPROVED, Status.REJECTED})
# Оператор видит заявку, только если её хотя бы раз отправили на рассмотрение
OPERATOR_VISIBLE_STATUSES = frozenset(
    {Status.SUBMITTED, Status.APPROVED, Status.REJECTED, Status.RETURNED}
)

STATUS_LABELS = {
    Status.DRAFT: "Черновик",
    Status.PAID: "Оплачена",
    Status.SUBMITTED: "На рассмотрении",
    Status.APPROVED: "Одобрена",
    Status.REJECTED: "Отклонена",
    Status.RETURNED: "Возвращена на доработку",
}

_ACTION_LABELS = {
    Action.PAY: "оплатить",
    Action.SUBMIT: "отправить на рассмотрение",
    Action.APPROVE: "одобрить",
    Action.REJECT: "отклонить",
    Action.RETURN: "вернуть на доработку",
}


class InvalidTransitionError(ConflictError):
    code = "INVALID_STATUS_TRANSITION"


def ensure_role_allowed(action: ApplicationAction, role: UserRole) -> None:
    """Действие в принципе не для этой роли (например, заявитель одобряет) — 403."""
    if action not in _ACTIONS_BY_ROLE[role]:
        raise ForbiddenError(
            f"Действие «{_ACTION_LABELS[action]}» недоступно для вашей роли",
            code="ACTION_FORBIDDEN_FOR_ROLE",
        )


def get_transition(
    status: ApplicationStatus,
    action: ApplicationAction,
    role: UserRole,
    comment: str | None = None,
) -> Transition:
    """Проверяет переход и возвращает его. Иначе бросает ошибку с причиной.

    Порядок проверок: сначала роль (действие в принципе не для этой роли — 403),
    затем статус (действие не из этого статуса — 409), затем комментарий (422).
    """
    ensure_role_allowed(action, role)

    transition = _TRANSITIONS_BY_KEY.get((status, action))
    if transition is None:
        raise InvalidTransitionError(
            f"Нельзя {_ACTION_LABELS[action]} заявку в статусе «{STATUS_LABELS[status]}»",
            details={"status": status.value, "action": action.value},
        )

    if transition.comment_required and not (comment and comment.strip()):
        raise BusinessValidationError(
            "Для этого решения нужен комментарий",
            code="COMMENT_REQUIRED",
            details=[{"field": "comment", "message": "Обязательное поле"}],
        )
    return transition


def allowed_transitions(status: ApplicationStatus, role: UserRole) -> list[ApplicationAction]:
    """Действия, которые роль может выполнить из этого статуса (без учёта проверок по БД)."""
    return [t.action for t in TRANSITIONS if t.source == status and t.role == role]
