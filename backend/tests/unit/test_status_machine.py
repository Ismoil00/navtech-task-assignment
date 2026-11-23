"""Unit-тесты машины состояний заявки.

Требование ТЗ: набор статусов и переходы проектируем сами, недопустимые
переходы отклоняет сервер. При отклонении и возврате комментарий обязателен.
После возврата повторно платить не нужно.
"""

import itertools

import pytest

from app.core.errors import BusinessValidationError, ForbiddenError
from app.domain.enums import ApplicationAction as Action
from app.domain.enums import ApplicationStatus as Status
from app.domain.enums import UserRole as Role
from app.domain.status_machine import (
    DELETABLE_STATUSES,
    EDITABLE_STATUSES,
    OPERATOR_VISIBLE_STATUSES,
    TERMINAL_STATUSES,
    InvalidTransitionError,
    allowed_transitions,
    get_transition,
)

# Ожидаемые переходы выписаны отдельно от таблицы в коде:
# если кто-то изменит правила в status_machine.py, тест это заметит.
EXPECTED_TRANSITIONS = {
    (Status.DRAFT, Action.PAY, Role.APPLICANT): Status.PAID,
    (Status.PAID, Action.SUBMIT, Role.APPLICANT): Status.SUBMITTED,
    (Status.RETURNED, Action.SUBMIT, Role.APPLICANT): Status.SUBMITTED,
    (Status.SUBMITTED, Action.APPROVE, Role.OPERATOR): Status.APPROVED,
    (Status.SUBMITTED, Action.REJECT, Role.OPERATOR): Status.REJECTED,
    (Status.SUBMITTED, Action.RETURN, Role.OPERATOR): Status.RETURNED,
}
ROLE_ACTIONS = {
    Role.APPLICANT: {Action.PAY, Action.SUBMIT},
    Role.OPERATOR: {Action.APPROVE, Action.REJECT, Action.RETURN},
}
COMMENT = "Не хватает печати на документе"


@pytest.mark.parametrize(
    ("status", "action", "role"),
    list(itertools.product(Status, Action, Role)),
    ids=lambda value: value.value,
)
def test_every_status_action_role_combination(status: Status, action: Action, role: Role) -> None:
    expected_target = EXPECTED_TRANSITIONS.get((status, action, role))

    if expected_target is not None:
        assert get_transition(status, action, role, COMMENT).target == expected_target
    elif action not in ROLE_ACTIONS[role]:
        # действие чужой роли — запрещено независимо от статуса
        with pytest.raises(ForbiddenError):
            get_transition(status, action, role, COMMENT)
    else:
        with pytest.raises(InvalidTransitionError) as error:
            get_transition(status, action, role, COMMENT)
        assert error.value.status_code == 409
        assert error.value.code == "INVALID_STATUS_TRANSITION"


@pytest.mark.parametrize("action", [Action.REJECT, Action.RETURN])
@pytest.mark.parametrize("comment", [None, "", "   "])
def test_reject_and_return_require_comment(action: Action, comment: str | None) -> None:
    with pytest.raises(BusinessValidationError) as error:
        get_transition(Status.SUBMITTED, action, Role.OPERATOR, comment)
    assert error.value.code == "COMMENT_REQUIRED"


def test_approve_does_not_require_comment() -> None:
    transition = get_transition(Status.SUBMITTED, Action.APPROVE, Role.OPERATOR)
    assert transition.target == Status.APPROVED


def test_returned_application_is_resubmitted_without_new_payment() -> None:
    assert allowed_transitions(Status.RETURNED, Role.APPLICANT) == [Action.SUBMIT]
    with pytest.raises(InvalidTransitionError):
        get_transition(Status.RETURNED, Action.PAY, Role.APPLICANT)


@pytest.mark.parametrize("status", sorted(TERMINAL_STATUSES))
@pytest.mark.parametrize("role", list(Role))
def test_terminal_statuses_have_no_way_out(status: Status, role: Role) -> None:
    assert allowed_transitions(status, role) == []


@pytest.mark.parametrize(
    ("status", "role", "expected"),
    [
        (Status.DRAFT, Role.APPLICANT, [Action.PAY]),
        (Status.PAID, Role.APPLICANT, [Action.SUBMIT]),
        (Status.SUBMITTED, Role.APPLICANT, []),
        (Status.SUBMITTED, Role.OPERATOR, [Action.APPROVE, Action.REJECT, Action.RETURN]),
        (Status.DRAFT, Role.OPERATOR, []),
        (Status.PAID, Role.OPERATOR, []),
    ],
)
def test_allowed_transitions(status: Status, role: Role, expected: list[Action]) -> None:
    assert allowed_transitions(status, role) == expected


def test_edit_and_delete_rules() -> None:
    assert EDITABLE_STATUSES == {Status.DRAFT, Status.RETURNED}
    assert DELETABLE_STATUSES == {Status.DRAFT}


def test_operator_sees_only_sent_applications() -> None:
    assert OPERATOR_VISIBLE_STATUSES == {
        Status.SUBMITTED,
        Status.APPROVED,
        Status.REJECTED,
        Status.RETURNED,
    }
