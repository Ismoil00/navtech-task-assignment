import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_hash_for_update(self, token_hash: str) -> RefreshToken | None:
        # FOR UPDATE: два одновременных обновления одним токеном выполняются по очереди
        return await self._session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash).with_for_update()
        )

    def add(self, token: RefreshToken) -> None:
        self._session.add(token)

    async def revoke_all_for_user(self, user_id: uuid.UUID, revoked_at: datetime) -> None:
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=revoked_at)
        )
