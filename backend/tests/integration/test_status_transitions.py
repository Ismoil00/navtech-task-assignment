"""Интеграционные тесты переходов статусов через API.

Требования ТЗ:
- набор статусов и переходы проектируем сами; недопустимые переходы
  отклоняет сервер, а не только интерфейс;
- оператор одобряет, отклоняет или возвращает на доработку, при отклонении
  и возврате комментарий обязателен;
- после возврата заявитель правит заявку и отправляет снова, платить второй
  раз не нужно;
- по каждой заявке видно, кто и когда менял её статус.
"""

import asyncio
from datetime import datetime

import pytest

from tests.integration.api import Actor, Api, payments_of
from tests.integration.conftest import FakeGateway, wait_until


async def test_return_then_resubmit_without_second_payment(
    api: Api, applicant: Actor, operator: Actor, gateway: FakeGateway
) -> None:
    application_id = await api.submitted_application(applicant)

    returned = await api.decide(operator, application_id, "return", "Скан нечитаемый")
    assert returned.status_code == 200
    assert returned.json()["status"] == "returned"

    # заявитель исправляет заявку: меняет комментарий и документ
    assert (
        await api.edit(applicant, application_id, comment="Загрузил новый скан")
    ).status_code == 200
    assert (await api.upload(applicant, application_id, "new-scan.pdf")).status_code == 200

    resubmitted = await api.submit(applicant, application_id)
    assert resubmitted.status_code == 200
    assert resubmitted.json()["status"] == "submitted"
    # повторная отправка не потребовала оплаты
    assert len(gateway.charges) == 1
    assert len(await payments_of(application_id)) == 1

    approved = await api.decide(operator, application_id, "approve")
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"


async def test_history_shows_who_and_when(api: Api, applicant: Actor, operator: Actor) -> None:
    application_id = await api.submitted_application(applicant)
    await api.decide(operator, application_id, "return", "Нужен другой скан")
    await api.submit(applicant, application_id)
    await api.decide(operator, application_id, "reject", "Документ недействителен")

    history = (await api.get(applicant, application_id)).json()["history"]

    assert [(h["from_status"], h["to_status"], h["actor"]["role"]) for h in history] == [
        (None, "draft", "applicant"),
        ("draft", "paid", "applicant"),
        ("paid", "submitted", "applicant"),
        ("submitted", "returned", "operator"),
        ("returned", "submitted", "applicant"),
        ("submitted", "rejected", "operator"),
    ]
    assert history[3]["actor"]["full_name"] == "Сафаров Далер Олимович"
    assert history[3]["comment"] == "Нужен другой скан"
    times = [datetime.fromisoformat(h["created_at"]) for h in history]
    assert times == sorted(times)


@pytest.mark.parametrize("action", ["reject", "return"])
@pytest.mark.parametrize("comment", [None, "", "   "])
async def test_reject_and_return_require_comment(
    api: Api, applicant: Actor, operator: Actor, action: str, comment: str | None
) -> None:
    application_id = await api.submitted_application(applicant)

    response = await api.decide(operator, application_id, action, comment)

    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["field"] == "comment"
    assert (await api.operator_get(operator, application_id)).json()["status"] == "submitted"


async def test_server_rejects_invalid_transitions(
    api: Api, applicant: Actor, operator: Actor
) -> None:
    application_id = await api.submitted_application(applicant)

    # повторная отправка уже отправленной заявки
    resubmit = await api.submit(applicant, application_id)
    assert resubmit.status_code == 409
    assert resubmit.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"

    # правка после отправки
    edit = await api.edit(applicant, application_id, comment="поздно")
    assert edit.status_code == 409
    assert edit.json()["error"]["code"] == "APPLICATION_NOT_EDITABLE"

    # решение по уже решённой заявке
    await api.decide(operator, application_id, "approve")
    for action, comment in [("approve", None), ("reject", "Передумали"), ("return", "Ещё раз")]:
        response = await api.decide(operator, application_id, action, comment)
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"


async def test_roles_cannot_perform_each_others_actions(
    api: Api, applicant: Actor, operator: Actor
) -> None:
    application_id = await api.submitted_application(applicant)

    applicant_decides = await api.decide(applicant, application_id, "approve")
    operator_submits = await api.submit(operator, application_id)

    assert applicant_decides.status_code == 403
    assert operator_submits.status_code == 403
    assert (await api.get(applicant, application_id)).json()["status"] == "submitted"


async def test_concurrent_decisions_only_one_wins(
    api: Api, applicant: Actor, operator: Actor, gateway: FakeGateway
) -> None:
    """Два оператора решают одновременно: второй получает 409, а не перезаписывает решение."""
    application_id = await api.submitted_application(applicant)
    release_refund = gateway.hold_refunds()

    # первое решение «застряло» внутри транзакции на возврате денег
    reject = asyncio.create_task(api.decide(operator, application_id, "reject", "Не подходит"))
    await wait_until(lambda: len(gateway.refunds) == 1)
    approve = asyncio.create_task(api.decide(operator, application_id, "approve"))
    await asyncio.sleep(0.2)  # второй запрос успевает дойти до заблокированной строки
    release_refund.set()

    assert (await reject).status_code == 200
    second = await approve
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"
    history = (await api.get(applicant, application_id)).json()["history"]
    assert history[-1]["to_status"] == "rejected"
    assert [h["from_status"] for h in history].count("submitted") == 1
