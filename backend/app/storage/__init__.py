from app.storage.base import StorageBackend
from app.storage.local import LocalStorage
from app.core.config import get_settings


def get_storage() -> StorageBackend:
    s = get_settings()
    if s.storage_backend == "local":
        return LocalStorage(s.storage_local_root)
    raise NotImplementedError(f"storage backend not implemented: {s.storage_backend}")
