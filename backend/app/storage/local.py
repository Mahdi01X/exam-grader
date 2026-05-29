from pathlib import Path
from typing import BinaryIO
from app.storage.base import StorageBackend


class LocalStorage(StorageBackend):
    def __init__(self, root: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, relative_path: str) -> Path:
        # Empêche l'évasion de répertoire (path traversal)
        p = (self.root / relative_path).resolve()
        if not str(p).startswith(str(self.root.resolve())):
            raise ValueError("path traversal blocked")
        return p

    def save(self, relative_path: str, data: BinaryIO) -> str:
        dst = self._resolve(relative_path)
        dst.parent.mkdir(parents=True, exist_ok=True)
        # NOTE: pour activer le chiffrement au repos, intercale ici un wrapper
        # de chiffrement (AES-GCM avec clé fournie par KMS).
        with open(dst, "wb") as f:
            while chunk := data.read(1024 * 1024):
                f.write(chunk)
        return relative_path

    def open(self, relative_path: str) -> BinaryIO:
        return open(self._resolve(relative_path), "rb")

    def absolute(self, relative_path: str) -> Path:
        return self._resolve(relative_path)

    def delete(self, relative_path: str) -> None:
        p = self._resolve(relative_path)
        if p.exists():
            p.unlink()
