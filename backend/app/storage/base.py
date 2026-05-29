from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO


class StorageBackend(ABC):
    """Interface de stockage pour fichiers de copies et de barèmes.

    L'implémentation locale écrit sur disque. Une implémentation S3 peut être
    branchée plus tard sans toucher au reste de l'application.

    Chiffrement au repos: à brancher ici (envelope encryption avec clé KMS).
    """

    @abstractmethod
    def save(self, relative_path: str, data: BinaryIO) -> str:
        """Sauvegarde un flux binaire. Retourne le chemin absolu/URI logique."""

    @abstractmethod
    def open(self, relative_path: str) -> BinaryIO: ...

    @abstractmethod
    def absolute(self, relative_path: str) -> Path: ...

    @abstractmethod
    def delete(self, relative_path: str) -> None: ...
