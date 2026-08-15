"""Session-scoped temporary storage for Streamlit uploads."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path


class JobStorage:
    def __init__(self):
        self._temporary_directory = tempfile.TemporaryDirectory(prefix="audiobook-mvp-")
        self.root = Path(self._temporary_directory.name)

    def save_bytes(self, name: str, content: bytes) -> Path:
        safe_name = Path(name).name or "upload.bin"
        destination = self.root / safe_name
        destination.write_bytes(content)
        return destination

    def clear(self) -> None:
        self._temporary_directory.cleanup()

    def __del__(self):
        try:
            self._temporary_directory.cleanup()
        except Exception:
            pass
