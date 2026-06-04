"""
File-backed JSON state store for Hermes Multi-Agent Harness v1.

All writes are atomic.  Each job has its own JSON file.
Default state directory: /tmp/harness/state/
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from harness.atomic_io import atomic_json_write
from harness.job_models import HarnessError, HarnessJob, HarnessResult, JobStatus

_DEFAULT_STATE_DIR = Path("/tmp/harness/state")


class StateStore:
    def __init__(self, state_dir: Path | str | None = None) -> None:
        self.state_dir = Path(state_dir) if state_dir else _DEFAULT_STATE_DIR
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, job_id: str) -> Path:
        return self.state_dir / f"{job_id}.json"

    def _load(self, job_id: str) -> dict:
        p = self._path(job_id)
        if not p.exists():
            raise FileNotFoundError(f"No job record for job_id={job_id!r}")
        return json.loads(p.read_text(encoding="utf-8"))

    def create_job_record(self, job: HarnessJob) -> None:
        """Write the initial queued record for *job*."""
        record = {
            "job_id":            job.job_id,
            "status":            JobStatus.queued.value,
            "tasks":             [t.model_dump() for t in job.tasks],
            "metadata":          job.metadata,
            "created_at":        datetime.now(timezone.utc).isoformat(),
            "updated_at":        None,
            "finalised_at":      None,
            "validation_errors": [],
            "result":            None,
        }
        atomic_json_write(self._path(job.job_id), record)

    def update_job_status(self, job_id: str, status: JobStatus) -> None:
        record = self._load(job_id)
        record["status"]     = status.value
        record["updated_at"] = datetime.now(timezone.utc).isoformat()
        atomic_json_write(self._path(job_id), record)

    def append_validation_error(self, job_id: str, error: HarnessError) -> None:
        record = self._load(job_id)
        record.setdefault("validation_errors", []).append(error.model_dump())
        atomic_json_write(self._path(job_id), record)

    def write_final_result(self, result: HarnessResult) -> None:
        record = self._load(result.job_id)
        record["status"]       = result.status.value
        record["result"]       = result.model_dump()
        record["finalised_at"] = datetime.now(timezone.utc).isoformat()
        atomic_json_write(self._path(result.job_id), record)

    def read_job_record(self, job_id: str) -> dict:
        return self._load(job_id)
