"""P8 CMS persistence layer.

JSON-file-based storage with atomic writes (write-temp, validate, rename).
No database. All state is project-local under domain/cms/data/.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


class PersistenceError(Exception):
    """Raised when persistence operation fails."""


class JSONStore:
    """Atomic JSON file store."""

    def __init__(self, base_path: str | Path) -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        return self.base_path / f"{name}.json"

    def _atomic_write(self, path: Path, data: Any) -> None:
        """Write atomically: write to temp, then rename."""
        fd, tmp_path = tempfile.mkstemp(
            dir=str(path.parent), prefix=".tmp_", suffix=".json"
        )
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def save(self, name: str, data: Any) -> None:
        """Save data atomically."""
        path = self._path(name)
        self._atomic_write(path, data)

    def load(self, name: str, default: Any = None) -> Any:
        """Load data or return default if not found."""
        path = self._path(name)
        if not path.exists():
            return default
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            raise PersistenceError(f"Failed to load {name}: {e}") from e

    def append(self, name: str, entry: Any) -> None:
        """Append to a JSON Lines file."""
        path = self.base_path / f"{name}.jsonl"
        line = json.dumps(entry, separators=(",", ":")) + "\n"
        with open(path, "a") as f:
            f.write(line)

    def read_lines(self, name: str) -> list[Any]:
        """Read all lines from a JSON Lines file."""
        path = self.base_path / f"{name}.jsonl"
        if not path.exists():
            return []
        entries = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries

    def delete(self, name: str) -> None:
        """Delete a stored file."""
        path = self._path(name)
        if path.exists():
            path.unlink()

    def exists(self, name: str) -> bool:
        """Check if a stored file exists."""
        return self._path(name).exists()

    def list_names(self) -> list[str]:
        """List all stored names."""
        names = []
        for f in self.base_path.glob("*.json"):
            names.append(f.stem)
        return sorted(names)
