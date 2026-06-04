"""
Read-only research tool adapter for Hermes Multi-Agent Harness v1.

Provides a local file metadata inspection tool that is:
- read-only (never modifies files)
- path-restricted (only within harness project root)
- content-safe (no content extraction unless explicitly safe)
- validated (Pydantic input/output)

This is the first safe, guardrailed Hermes tool adapter.
"""
from __future__ import annotations

import os
import stat
import time
from datetime import datetime, timezone
from pathlib import Path

from harness.job_models import RoleType, SafetyConfig, ToolCategory, AuditEvent
from harness.validators import validate_tool_access

_HARNESS_ROOT = Path("/home/jfroh/hermes/harness").resolve()

# Files that are never safe to inspect even for metadata
_BLOCKED_FILENAMES = {
    ".env", ".env.example", ".env.local", ".env.production",
    "key", "keys", "id_rsa", "id_ed25519", "id_ecdsa",
    "credentials", "credentials.json", "secret", "secrets",
    ".secret", ".secrets", "token", "tokens", ".token",
    "auth", "auth.json", "password", "passwd",
}

_BLOCKED_EXTENSIONS = {".key", ".pem", ".p12", ".pfx", ".pkcs12",
                       ".crt", ".cert", ".ca-bundle"}


class ReadOnlyFileMetadataInput:
    """Input model for the read-only file metadata tool."""

    def __init__(
        self,
        path: str,
        safety_config: SafetyConfig | None = None,
        audit_event: AuditEvent | None = None,
    ):
        self.path = path
        self.safety_config = safety_config or SafetyConfig()
        self.audit_event = audit_event

    def __repr__(self) -> str:
        return f"ReadOnlyFileMetadataInput(path={self.path!r})"


class ReadOnlyFileMetadataOutput:
    """Output model from the read-only file metadata tool."""

    def __init__(
        self,
        task_id: str,
        role_type: RoleType,
        metadata: dict | None = None,
        error_message: str | None = None,
        blocked: bool = False,
    ):
        self.task_id = task_id
        self.role_type = role_type
        self.metadata = metadata or {}
        self.error_message = error_message
        self.blocked = blocked
        self.success = error_message is None and not blocked

    def to_agent_output(self) -> dict:
        """Convert to AgentOutput-compatible result dict."""
        return {
            "task_id": self.task_id,
            "role_type": self.role_type.value,
            "result": {
                "blocked": self.blocked,
                "metadata": self.metadata if self.success else {},
                "error": self.error_message,
            },
            "success": self.success,
            "error_message": self.error_message,
        }

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "role_type": self.role_type.value,
            "metadata": self.metadata if self.success else {},
            "error_message": self.error_message,
            "blocked": self.blocked,
            "success": self.success,
        }


def _is_blocked_filename(path: Path) -> bool:
    """Check if the filename or stem matches a blocked pattern."""
    name = path.name.lower()
    stem = path.stem.lower()
    return name in _BLOCKED_FILENAMES or stem in _BLOCKED_FILENAMES


def _is_blocked_extension(path: Path) -> bool:
    return path.suffix.lower() in _BLOCKED_EXTENSIONS


def _is_symlink_escaping(root: Path, target: Path) -> bool:
    """Check if a resolved symlink would escape the harness root."""
    try:
        resolved = target.resolve(strict=False)
    except (OSError, RuntimeError):
        return True
    try:
        root_resolved = root.resolve()
    except (OSError, RuntimeError):
        return True
    return not str(resolved).startswith(str(root_resolved))


def inspect_file_metadata(
    task_id: str,
    relative_path: str,
    safety_config: SafetyConfig | None = None,
    audit_event: AuditEvent | None = None,
) -> ReadOnlyFileMetadataOutput:
    """
    Inspect a file's metadata, returning only safe attributes.

    This is the core read-only research tool function.

    Guards checked:
    - SafetyConfig.guardrail check via validate_tool_access()
    - Path must resolve inside HARNESS_ROOT
    - Symlinks must not escape HARNESS_ROOT
    - No directories
    - No blocked file names (.env, keys, credentials, etc.)
    - No blocked extensions (.key, .pem, .p12, etc.)
    """
    config = safety_config or SafetyConfig()
    output = ReadOnlyFileMetadataOutput(
        task_id=task_id,
        role_type=RoleType.research,
    )

    # Step 1: Guardrail check
    allowed, guardrail_msg = validate_tool_access(
        config, RoleType.research, ToolCategory.research,
        has_audit_context=(audit_event is not None),
    )
    if not allowed:
        output.blocked = True
        output.error_message = f"Guardrail blocked: {guardrail_msg}"
        return output

    # Step 2: Resolve and validate path
    request_path = Path(relative_path)

    # Reject absolute paths (must be relative to harness root)
    if request_path.is_absolute():
        output.blocked = True
        output.error_message = (
            f"Blocked: absolute path {relative_path!r} is not allowed. "
            f"Use a relative path from the harness root."
        )
        return output

    # Reject paths with '..' components that escape root
    try:
        resolved = (_HARNESS_ROOT / request_path).resolve()
    except (OSError, RuntimeError):
        output.blocked = True
        output.error_message = f"Blocked: cannot resolve path {relative_path!r}"
        return output

    # Check symlink escape
    if request_path.is_symlink():
        if _is_symlink_escaping(_HARNESS_ROOT, request_path):
            output.blocked = True
            output.error_message = (
                f"Blocked: symlink {relative_path!r} escapes harness root"
            )
            return output
        # Also check symlink resolves inside root
        try:
            real = os.path.realpath(str(_HARNESS_ROOT / request_path))
            if not real.startswith(str(_HARNESS_ROOT)):
                output.blocked = True
                output.error_message = (
                    f"Blocked: symlink {relative_path!r} resolves outside harness root"
                )
                return output
        except (OSError, RuntimeError):
            output.blocked = True
            output.error_message = (
                f"Blocked: cannot resolve symlink {relative_path!r}"
            )
            return output

    # Reject paths outside harness root
    resolved_str = str(resolved)
    if not resolved_str.startswith(str(_HARNESS_ROOT)):
        output.blocked = True
        output.error_message = (
            f"Blocked: path {relative_path!r} resolves outside harness root"
        )
        return output

    # Reject directories
    if resolved.is_dir():
        output.blocked = True
        output.error_message = (
            f"Blocked: {relative_path!r} is a directory; only files are allowed"
        )
        return output

    # Reject blocked filenames
    rel = Path(relative_path)
    if _is_blocked_filename(rel) or _is_blocked_extension(rel):
        output.blocked = True
        output.error_message = (
            f"Blocked: file {relative_path!r} matches blocked filename or extension"
        )
        return output

    # Step 3: Gather metadata (read-only)
    if not resolved.exists():
        output.metadata = {"exists": False, "path": relative_path}
        output.success = True
        return output

    try:
        st = resolved.stat()
    except OSError as e:
        output.blocked = True
        output.error_message = f"Error reading file metadata: {e}"
        return output

    is_symlink = resolved.is_symlink()
    is_text_like = _is_text_file(resolved)

    metadata = {
        "exists": True,
        "path": relative_path,
        "size_bytes": st.st_size,
        "extension": resolved.suffix,
        "is_symlink": is_symlink,
        "is_directory": False,
        "last_modified": datetime.fromtimestamp(
            st.st_mtime, tz=timezone.utc
        ).isoformat(),
        "created": datetime.fromtimestamp(
            st.st_ctime, tz=timezone.utc
        ).isoformat(),
    }

    # Only for safe text files: add line count
    if is_text_like and st.st_size > 0:
        try:
            text = resolved.read_text(encoding="utf-8", errors="replace")
            metadata["line_count"] = text.count("\n") + (0 if text.endswith("\n") else 1)
            # Truncated preview for small files only
            if st.st_size < 10000:
                metadata["preview_chars"] = text[:200]
        except (OSError, UnicodeDecodeError):
            metadata["line_count"] = None

    output.metadata = metadata
    output.success = True
    return output


def _is_text_file(path: Path) -> bool:
    """Heuristic: check if a file extension looks like a text file."""
    text_extensions = {
        ".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".cfg",
        ".ini", ".conf", ".csv", ".tsv", ".xml", ".html", ".htm", ".css",
        ".js", ".ts", ".jsx", ".tsx", ".sh", ".bash", ".zsh", ".env",
        ".rst", ".log", ".gitignore", ".dockerignore",
    }
    return path.suffix.lower() in text_extensions