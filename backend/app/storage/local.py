import re
from collections.abc import AsyncIterable, AsyncIterator

import anyio

_CHUNK_SIZE = 64 * 1024
# Ключи генерирует сервер (uuid4.hex). Проверка формата исключает выход за пределы
# каталога вида "../../etc/passwd", даже если ключ когда-нибудь придёт извне.
_KEY_PATTERN = re.compile(r"^[0-9a-f]{32}$")


class LocalFileStorage:
    def __init__(self, root: str) -> None:
        self._root = anyio.Path(root)

    async def save(self, key: str, chunks: AsyncIterable[bytes]) -> None:
        await self._root.mkdir(parents=True, exist_ok=True)
        target = self._path(key)
        # пишем во временный файл и переименовываем: недописанный файл не появится под ключом
        partial = target.with_suffix(".part")
        try:
            async with await anyio.open_file(partial, "wb") as file:
                async for chunk in chunks:
                    await file.write(chunk)
            await partial.rename(target)
        except BaseException:
            await partial.unlink(missing_ok=True)
            raise

    async def read(self, key: str) -> AsyncIterator[bytes]:
        async with await anyio.open_file(self._path(key), "rb") as file:
            while chunk := await file.read(_CHUNK_SIZE):
                yield chunk

    async def exists(self, key: str) -> bool:
        return await self._path(key).is_file()

    async def delete(self, key: str) -> None:
        await self._path(key).unlink(missing_ok=True)

    def _path(self, key: str) -> anyio.Path:
        if not _KEY_PATTERN.fullmatch(key):
            raise ValueError(f"Недопустимый ключ файла: {key!r}")
        return self._root / key
