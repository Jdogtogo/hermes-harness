"""
Atomic JSON write helper.

Write sequence: temp file → flush → fsync (best-effort) → os.replace().
A partial write can never overwrite an existing file.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Union


def atomic_json_write(path: Union[str, Path], data: Any) -> None:
    """Write *data* as JSON to *path* atomically."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp.json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, default=str)
            fh.flush()
            try:
                os.fsync(fh.fileno())
            except OSError:
                pass  # fsync is best-effort; not available on all filesystems
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def atomic_json_read(path: Union[str, Path]) -> Any:
    """Return parsed JSON from *path*."""
    return json.loads(Path(path).read_text(encoding="utf-8"))
