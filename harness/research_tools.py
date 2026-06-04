"""
Read-only file metadata tool for ResearchAgent.
Allowed root: /home/jfroh/hermes/harness/
Returns only structural metadata — never content, previews, or secrets.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

HARNESS_ROOT: Path = Path("/home/jfroh/hermes/harness").resolve()

_BLOCKED_EXTENSIONS: frozenset[str] = frozenset({
    ".env", ".pem", ".p12", ".key", ".pfx", ".crt", ".cer",
    ".jks", ".keystore", ".gpg", ".pgp", ".der",
})

_BLOCKED_STEMS: frozenset[str] = frozenset({
    ".env", ".htpasswd", ".netrc", ".npmrc", ".pypirc",
    "credentials", "secrets", "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519",
})

_BLOCKED_NAME_PATTERN: re.Pattern[str] = re.compile(
    r"(secret|credential|password|passwd|token|apikey|api[_-]key"
    r"|private[_-]key|access[_-]key|auth[_-]?key)",
    re.IGNORECASE,
)

_SAFE_TEXT_EXTENSIONS: frozenset[str] = frozenset({
    ".py", ".txt", ".md", ".rst", ".yaml", ".yml", ".toml",
    ".cfg", ".ini", ".json", ".csv", ".log", ".sh", ".conf",
})

_MAX_LINE_COUNT_BYTES: int = 10 * 1024 * 1024  # 10 MB


def _is_credential_like(name: str) -> bool:
    """Return True if the filename looks like a secret or credential file."""
    lower = name.lower()
    stem = Path(name).stem.lower()
    suffix = Path(name).suffix.lower()
    if suffix in _BLOCKED_EXTENSIONS:
        return True
    if lower in _BLOCKED_STEMS or stem in _BLOCKED_STEMS:
        return True
    if _BLOCKED_NAME_PATTERN.search(name):
        return True
    return False


def inspect_file_metadata(path: str) -> dict:
    """
    Return read-only structural metadata for a file under HARNESS_ROOT.

    Allowed outputs: exists, resolved_path, size_bytes, extension,
                     last_modified, line_count (safe text files only).
    Never returns file content, previews, snippets, or binary data.
    Rejects: path traversal, absolute escapes, symlink escapes, directories,
             .env/credential/key/pem/p12 files.
    """
    if not isinstance(path, str):
        return {"status": "denied", "reason": "path must be a string"}

    stripped = path.strip()
    if not stripped:
        return {"status": "denied", "reason": "path must not be empty"}

    try:
        requested = Path(stripped)
    except Exception:
        return {"status": "denied", "reason": "invalid path"}

    # Reject explicit path-traversal components before any resolution
    raw_parts = requested.parts
    if ".." in raw_parts:
        return {"status": "denied", "reason": "path traversal rejected"}

    # Build the candidate path
    if requested.is_absolute():
        candidate = requested
    else:
        candidate = HARNESS_ROOT / requested

    # Resolve symlinks and canonicalise
    try:
        resolved = candidate.resolve()
    except Exception:
        return {"status": "denied", "reason": "path resolution failed"}

    # Reject if resolved path escapes harness root (catches symlink escapes)
    try:
        resolved.relative_to(HARNESS_ROOT)
    except ValueError:
        return {"status": "denied", "reason": "path outside harness root rejected"}

    # Reject directories
    if resolved.is_dir():
        return {"status": "denied", "reason": "directories are not allowed"}

    # Reject credential/key/secret files by name
    if _is_credential_like(resolved.name):
        return {"status": "denied", "reason": "credential or key file rejected"}

    # File does not exist — safe to report that fact
    if not resolved.exists():
        return {
            "status": "ok",
            "exists": False,
            "resolved_path": str(resolved),
        }

    stat = resolved.stat()
    size_bytes: int = stat.st_size
    extension: str = resolved.suffix.lower()
    last_modified: str = datetime.fromtimestamp(
        stat.st_mtime, tz=timezone.utc
    ).isoformat()

    result: dict = {
        "status": "ok",
        "exists": True,
        "resolved_path": str(resolved),
        "size_bytes": size_bytes,
        "extension": extension,
        "last_modified": last_modified,
    }

    # Line count only for recognised safe text formats within size limit
    if extension in _SAFE_TEXT_EXTENSIONS and size_bytes <= _MAX_LINE_COUNT_BYTES:
        try:
            with resolved.open("rb") as fh:
                result["line_count"] = sum(1 for _ in fh)
        except Exception:
            pass

    return result
