"""
Atomic JSON write helper.

Writes to a temp file in the same directory, flushes, fsyncs, then
uses os.replace() so a partial write can never corrupt an existing file.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Union


def atomic_json_write(path: Union[str, Path], data: Any) -> None:
    """
    Write *data* as JSON to *path* atomically.

    Sequence:
      1. Create a temp file in the same directory as the target.
      2. Write JSON, flush, fsync.
      3. os.replace() the temp file over the target.

    If anything fails before os.replace(), the original file is untouched.
    """
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
                # fsync is best-effort; some platforms/FSes don't support it
                pass
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def atomic_json_read(path: Union[str, Path]) -> Any:
    """Read and return parsed JSON from *path*."""
    return json.loads(Path(path).read_text(encoding="utf-8"))
