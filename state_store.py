"""
File-backed JSON state store for Hermes Multi-Agent Harness v1.

All writes are atomic (via atomic_writer.py) to prevent partial-write
corruption.  Each job gets its own JSON file under STATE_DIR.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from atomic_writer import atomic_json_write
from schema import HarnessError, HarnessJob, HarnessResult, JobStatus

STATE_DIR = Path("/tmp/harness/state")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _job_path(job_id: str) -> Path:
    return STATE_DIR / f"{job_id}.json"


def _ensure_state_dir() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def _load_record(job_id: str) -> dict:
    path = _job_path(job_id)
    if not path.exists():
        raise FileNotFoundError(f"No job record found for job_id={job_id!r}")
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_job_record(job: HarnessJob) -> None:
    """Create the initial job record with status=queued."""
    _ensure_state_dir()
    record = {
        "job_id": job.job_id,
        "status": JobStatus.queued.value,
        "tasks": [t.model_dump() for t in job.tasks],
        "metadata": job.metadata,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": None,
        "finalised_at": None,
        "validation_errors": [],
        "result": None,
    }
    atomic_json_write(_job_path(job.job_id), record)


def update_job_status(job_id: str, status: JobStatus) -> None:
    """Update the status field of an existing job record."""
    record = _load_record(job_id)
    record["status"] = status.value
    record["updated_at"] = datetime.now(timezone.utc).isoformat()
    atomic_json_write(_job_path(job_id), record)


def append_validation_error(job_id: str, error: HarnessError) -> None:
    """Append a validation error to the job record without overwriting it."""
    record = _load_record(job_id)
    record.setdefault("validation_errors", []).append(error.model_dump())
    atomic_json_write(_job_path(job_id), record)


def write_final_result(result: HarnessResult) -> None:
    """Write the final HarnessResult into the job record."""
    record = _load_record(result.job_id)
    record["status"] = result.status.value
    record["result"] = result.model_dump()
    record["finalised_at"] = datetime.now(timezone.utc).isoformat()
    atomic_json_write(_job_path(result.job_id), record)


def read_job_record(job_id: str) -> dict:
    """Return the raw job record dict for *job_id*."""
    return _load_record(job_id)
