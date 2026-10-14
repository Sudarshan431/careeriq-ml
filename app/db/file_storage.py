"""
Storage abstraction for uploaded resume files. The local implementation
writes to disk under a non-web-servable directory keyed by an opaque UUID
filename (never the user-supplied filename, to avoid path traversal and to
avoid leaking filesystem paths through the API). Swapping to S3/GCS later
means implementing this same interface -- callers never see a raw path.
"""
from __future__ import annotations

import uuid
from pathlib import Path

from app.core.config import settings
from app.utils.file_utils import sanitize_filename


class LocalResumeStorage:
    def __init__(self, base_dir: str | Path | None = None):
        self.base_dir = Path(base_dir or settings.data_dir) / "resumes"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, candidate_id: uuid.UUID, original_filename: str, file_bytes: bytes) -> str:
        """Returns an opaque storage_key (never a filesystem path) to persist on the Resume row."""
        ext = Path(sanitize_filename(original_filename)).suffix
        storage_key = f"{candidate_id}/{uuid.uuid4().hex}{ext}"
        target = self.base_dir / storage_key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(file_bytes)
        return storage_key

    def load(self, storage_key: str) -> bytes:
        target = self._resolve(storage_key)
        return target.read_bytes()

    def delete(self, storage_key: str) -> None:
        target = self._resolve(storage_key)
        target.unlink(missing_ok=True)

    def _resolve(self, storage_key: str) -> Path:
        # Defends against path traversal even though storage_key is
        # server-generated -- never trust a stored string blindly.
        resolved = (self.base_dir / storage_key).resolve()
        if not str(resolved).startswith(str(self.base_dir.resolve())):
            raise ValueError("Invalid storage key.")
        return resolved


resume_storage = LocalResumeStorage()
