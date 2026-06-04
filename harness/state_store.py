"""
File-backed JSON state store for Hermes Multi-Agent Harness v1.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from harness.atomic_io import atomic_json_write
from harness.job_models import AuditEvent, HarnessError, HarnessJob, HarnessResult, JobStatus

_DEFAULT_STATE_DIR = Path("/home/jfroh/hermes/harness/state")


class StateStoreError(Exception):
    """Base error for StateStore operations."""


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
        if p.stat().st_size == 0:
            raise StateStoreError(f"Job record {job_id!r} is zero-byte (corrupted)")
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise StateStoreError(
                f"Corrupted JSON in job record {job_id!r}: {exc}"
            ) from exc

    def create_job_record(self, job: HarnessJob) -> None:
        p = self._path(job.job_id)
        if p.exists():
            raise StateStoreError(
                f"Job record for job_id={job.job_id!r} already exists "
                f"at {p} — refusing to silently overwrite"
            )
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
            "audit_events":      [],
        }
        atomic_json_write(p, record)

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

    def write_audit_event(self, job_id: str, event: AuditEvent) -> None:
        self.append_audit_event(job_id, event)

    def append_audit_event(self, job_id: str, event: AuditEvent) -> None:
        record = self._load(job_id)
        events = record.setdefault("audit_events", [])
        events.append(event.model_dump())
        record["updated_at"] = datetime.now(timezone.utc).isoformat()
        atomic_json_write(self._path(job_id), record)

    def read_job_audit_events(self, job_id: str) -> list[dict]:
        record = self._load(job_id)
        return record.get("audit_events", [])

    def read_audit_log(self) -> list:
        audit_path = self.state_dir / "_audit_log.json"
        if not audit_path.exists():
            return []
        return json.loads(audit_path.read_text(encoding="utf-8"))

    def read_job_record(self, job_id: str) -> dict:
        return self._load(job_id)
