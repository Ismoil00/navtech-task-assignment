"""Короткие вызовы API для тестов, чтобы сценарии читались как шаги пользователя."""

import uuid
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy import select

from app.core.db import SessionFactory
from app.models import Payment, User

PDF = b"%PDF-1.7\n" + b"0" * 1024


@dataclass
class Actor:
    user: User
    headers: dict[str, str]


class Api:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    async def create_application(self, actor: Actor, **overrides: Any) -> dict[str, Any]:
        payload = {
            "full_name": "Каримов Фаррух Шарифович",
            "phone": "+992 93 123 4567",
            "service_type_id": 1,
            **overrides,
        }
        response = await self.client.post("/api/applications", json=payload, headers=actor.headers)
        assert response.status_code == 201, response.text
        return response.json()

    async def upload(
        self, actor: Actor, application_id: str, filename: str = "scan.pdf", content: bytes = PDF
    ) -> httpx.Response:
        return await self.client.put(
            f"/api/applications/{application_id}/file",
            files={"file": (filename, content, "application/pdf")},
            headers=actor.headers,
        )

    async def pay(
        self, actor: Actor, application_id: str, key: str | None = None
    ) -> httpx.Response:
        headers = {**actor.headers, "Idempotency-Key": key or uuid.uuid4().hex}
        return await self.client.post(
            f"/api/applications/{application_id}/payments", headers=headers
        )

    async def submit(self, actor: Actor, application_id: str) -> httpx.Response:
        return await self.client.post(
            f"/api/applications/{application_id}/submit", headers=actor.headers
        )

    async def get(self, actor: Actor, application_id: str) -> httpx.Response:
        return await self.client.get(f"/api/applications/{application_id}", headers=actor.headers)

    async def draft_with_file(self, actor: Actor, **overrides: Any) -> str:
        application = await self.create_application(actor, **overrides)
        response = await self.upload(actor, application["id"])
        assert response.status_code == 200, response.text
        return application["id"]

    async def paid_application(self, actor: Actor, **overrides: Any) -> str:
        application_id = await self.draft_with_file(actor, **overrides)
        response = await self.pay(actor, application_id)
        assert response.status_code == 200, response.text
        return application_id


async def payments_of(application_id: str) -> list[Payment]:
    async with SessionFactory() as session:
        result = await session.scalars(
            select(Payment)
            .where(Payment.application_id == uuid.UUID(application_id))
            .order_by(Payment.created_at)
        )
        return list(result.all())
