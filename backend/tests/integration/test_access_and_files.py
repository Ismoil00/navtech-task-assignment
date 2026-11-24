"""Интеграционные тесты доступа к заявкам, файлов и очереди оператора.

Требования ТЗ:
- заявитель видит только свои заявки, и это проверяется на сервере;
- файлы: тип и размер проверяются на сервере; чужой файл нельзя скачать,
  подобрав ссылку;
- оператор видит список отправленных заявок с фильтром по статусу и типу
  услуги, список постраничный; открывает заявку и скачивает приложенный файл.
"""

import uuid
from collections.abc import Awaitable, Callable

import httpx
import pytest

from app.domain.documents import MAX_DOCUMENT_SIZE
from tests.integration.api import PDF, Actor, Api

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 512
JPEG = b"\xff\xd8\xff\xe0" + b"0" * 512


# --- заявитель видит только свои заявки ---


async def test_applicant_lists_only_own_applications(
    api: Api, applicant: Actor, other_applicant: Actor
) -> None:
    await api.create_application(applicant)
    await api.create_application(applicant)
    await api.create_application(other_applicant)

    mine = (await api.client.get("/api/applications", headers=applicant.headers)).json()
    theirs = (await api.client.get("/api/applications", headers=other_applicant.headers)).json()

    assert mine["total"] == 2
    assert theirs["total"] == 1


OtherRequest = Callable[[Api, Actor, str], Awaitable[httpx.Response]]

OTHER_APPLICANT_REQUESTS: dict[str, OtherRequest] = {
    "details": lambda api, actor, app_id: api.get(actor, app_id),
    "edit": lambda api, actor, app_id: api.edit(actor, app_id, comment="чужая"),
    "upload": lambda api, actor, app_id: api.upload(actor, app_id),
    "download": lambda api, actor, app_id: api.client.get(
        f"/api/applications/{app_id}/file", headers=actor.headers
    ),
    "pay": lambda api, actor, app_id: api.pay(actor, app_id),
    "submit": lambda api, actor, app_id: api.submit(actor, app_id),
    "delete": lambda api, actor, app_id: api.client.delete(
        f"/api/applications/{app_id}", headers=actor.headers
    ),
}


@pytest.mark.parametrize("request_name", OTHER_APPLICANT_REQUESTS)
async def test_other_applicant_cannot_access_application(
    api: Api, applicant: Actor, other_applicant: Actor, request_name: str
) -> None:
    application_id = await api.paid_application(applicant)

    response = await OTHER_APPLICANT_REQUESTS[request_name](api, other_applicant, application_id)

    # 404, а не 403: чужая заявка для заявителя просто не существует
    assert response.status_code == 404
    assert (await api.get(applicant, application_id)).json()["status"] == "paid"


async def test_guessed_file_link_returns_404(api: Api, applicant: Actor, operator: Actor) -> None:
    guessed = uuid.uuid4()

    as_applicant = await api.client.get(
        f"/api/applications/{guessed}/file", headers=applicant.headers
    )
    as_operator = await api.client.get(
        f"/api/operator/applications/{guessed}/file", headers=operator.headers
    )

    assert as_applicant.status_code == as_operator.status_code == 404


async def test_file_requires_authentication(api: Api, applicant: Actor) -> None:
    application_id = await api.draft_with_file(applicant)

    response = await api.client.get(f"/api/applications/{application_id}/file")

    assert response.status_code == 401


# --- тип и размер файла проверяются на сервере ---


@pytest.mark.parametrize(
    ("filename", "content", "content_type"),
    [
        ("паспорт.pdf", PDF, "application/pdf"),
        ("photo.jpg", JPEG, "image/jpeg"),
        ("scan.png", PNG, "image/png"),
    ],
)
async def test_allowed_documents_are_accepted_and_downloaded_unchanged(
    api: Api, applicant: Actor, filename: str, content: bytes, content_type: str
) -> None:
    application = await api.create_application(applicant)

    uploaded = await api.upload(applicant, application["id"], filename, content)
    downloaded = await api.client.get(
        f"/api/applications/{application['id']}/file", headers=applicant.headers
    )

    assert uploaded.status_code == 200
    assert uploaded.json()["attachment"]["content_type"] == content_type
    assert downloaded.status_code == 200
    assert downloaded.content == content
    assert downloaded.headers["content-type"] == content_type


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("invoice.pdf", b"MZ\x90\x00" + b"0" * 512),  # исполняемый файл под видом PDF
        ("photo.png", PDF),  # PDF под видом картинки
        ("animation.gif", b"GIF89a" + b"0" * 512),
    ],
)
async def test_wrong_file_type_is_rejected(
    api: Api, applicant: Actor, filename: str, content: bytes
) -> None:
    application = await api.create_application(applicant)

    response = await api.upload(applicant, application["id"], filename, content)

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"
    assert (await api.get(applicant, application["id"])).json()["attachment"] is None


async def test_file_larger_than_5_mb_is_rejected(api: Api, applicant: Actor) -> None:
    application = await api.create_application(applicant)
    too_big = PDF + b"0" * (MAX_DOCUMENT_SIZE - len(PDF) + 1)

    response = await api.upload(applicant, application["id"], "big.pdf", too_big)

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "FILE_TOO_LARGE"
    assert (await api.get(applicant, application["id"])).json()["attachment"] is None


# --- очередь оператора ---


async def test_operator_sees_only_sent_applications(
    api: Api, applicant: Actor, operator: Actor
) -> None:
    draft = (await api.create_application(applicant))["id"]
    paid = await api.paid_application(applicant)
    submitted = await api.submitted_application(applicant)

    queue = (await api.queue(operator)).json()

    assert [item["id"] for item in queue["items"]] == [submitted]
    assert (await api.operator_get(operator, draft)).status_code == 404
    assert (await api.operator_get(operator, paid)).status_code == 404


async def test_operator_queue_filters_by_status_and_service_type(
    api: Api, applicant: Actor, operator: Actor
) -> None:
    certificate_1 = await api.submitted_application(applicant, service_type_id=1)
    certificate_2 = await api.submitted_application(applicant, service_type_id=1)
    apostille = await api.submitted_application(applicant, service_type_id=5)
    await api.decide(operator, certificate_2, "return", "Нужен другой скан")

    by_status = (await api.queue(operator, status="submitted")).json()
    by_service = (await api.queue(operator, service_type_id=1)).json()
    by_both = (await api.queue(operator, status="submitted", service_type_id=1)).json()

    assert {item["id"] for item in by_status["items"]} == {certificate_1, apostille}
    assert {item["id"] for item in by_service["items"]} == {certificate_1, certificate_2}
    assert [item["id"] for item in by_both["items"]] == [certificate_1]


async def test_operator_queue_is_paginated(api: Api, applicant: Actor, operator: Actor) -> None:
    submitted = {await api.submitted_application(applicant) for _ in range(5)}

    first = (await api.queue(operator, page=1, page_size=2)).json()
    second = (await api.queue(operator, page=2, page_size=2)).json()
    last = (await api.queue(operator, page=3, page_size=2)).json()

    assert first["total"] == 5
    assert first["pages"] == 3
    assert [len(page["items"]) for page in (first, second, last)] == [2, 2, 1]
    seen = {item["id"] for page in (first, second, last) for item in page["items"]}
    assert seen == submitted


async def test_operator_opens_application_and_downloads_document(
    api: Api, applicant: Actor, operator: Actor
) -> None:
    application_id = await api.submitted_application(applicant)

    card = await api.operator_get(operator, application_id)
    document = await api.client.get(
        f"/api/operator/applications/{application_id}/file", headers=operator.headers
    )

    assert card.status_code == 200
    assert card.json()["allowed_actions"] == ["approve", "reject", "return"]
    assert document.status_code == 200
    assert document.content == PDF
