from functools import cache

from app.core.config import get_settings
from app.storage.base import FileStorage
from app.storage.local import LocalFileStorage


@cache
def get_file_storage() -> FileStorage:
    return LocalFileStorage(get_settings().upload_dir)


__all__ = ["FileStorage", "LocalFileStorage", "get_file_storage"]
