"""Какие кнопки показать пользователю для заявки.

Список считается из тех же правил, что проверяет сервер при самом действии,
поэтому интерфейс не может предложить то, что сервер потом отклонит.
"""

from app.domain.enums import AllowedAction, PaymentStatus, UserRole
from app.domain.status_machine import DELETABLE_STATUSES, EDITABLE_STATUSES, allowed_transitions
from app.models import Application


def for_applicant(application: Application) -> list[AllowedAction]:
    # пока шлюз обрабатывает оплату, с заявкой ничего делать нельзя — ждём результата
    if any(payment.status == PaymentStatus.PROCESSING for payment in application.payments):
        return []

    actions: list[AllowedAction] = []
    if application.status in EDITABLE_STATUSES:
        actions += [AllowedAction.EDIT, AllowedAction.UPLOAD_FILE]
    if application.status in DELETABLE_STATUSES:
        actions.append(AllowedAction.DELETE)
    # оплатить и отправить можно только с приложенным документом
    if application.attachment is not None:
        actions += [
            AllowedAction(action.value)
            for action in allowed_transitions(application.status, UserRole.APPLICANT)
        ]
    return actions


def for_operator(application: Application) -> list[AllowedAction]:
    return [
        AllowedAction(action.value)
        for action in allowed_transitions(application.status, UserRole.OPERATOR)
    ]
