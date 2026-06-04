"""
Hermes Multi-Agent Harness v1 — Smoke Test

End-to-end path through the harness with no LLM calls:
  1. Build a HarnessJob with all three role types.
  2. Route through Supervisor.
  3. Write to StateStore.
  4. Read back and verify.
  5. Print pass/fail summary.

Usage:
    /tmp/harness_venv/bin/python /tmp/harness/run_harness_smoke_test.py
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

# Ensure harness package is importable when run directly
sys.path.insert(0, "/tmp/harness")

from harness.job_models  import HarnessJob, HarnessTask, JobStatus, RoleType
from harness.supervisor  import Supervisor
from harness.state_store import StateStore
from harness.validators  import validate_job

SMOKE_JOB_ID = "smoke-test-job-v1-001"

checks: list[tuple[str, bool, str]] = []

def check(name: str, cond: bool, detail: str = "") -> bool:
    checks.append((name, cond, detail))
    tag = "PASS" if cond else "FAIL"
    print(f"  [{tag}] {name}" + (f"  ({detail})" if detail else ""))
    return cond

def run() -> None:
    print("\n=== Hermes Multi-Agent Harness v1 — Smoke Test ===\n")

    # Step 1: Build job
    print("Step 1: Build HarnessJob")
    try:
        job = HarnessJob(
            job_id=SMOKE_JOB_ID,
            tasks=[
                HarnessTask(
                    task_id="smoke-research-01",
                    role_type=RoleType.research,
                    payload={"query": "Hermes gateway status?"},
                ),
                HarnessTask(
                    task_id="smoke-memory-01",
                    role_type=RoleType.memory_state,
                    payload={"operation": "read", "key": "hermes.last_run"},
                ),
                HarnessTask(
                    task_id="smoke-exec-01",
                    role_type=RoleType.execution,
                    payload={"action": "log_heartbeat"},
                ),
            ],
        )
        check("HarnessJob created (3 tasks)", len(job.tasks) == 3)
    except Exception as exc:
        check("HarnessJob creation", False, str(exc)); return

    # Step 2: Validate
    print("\nStep 2: Validate job")
    ok, errs = validate_job(job)
    check("validate_job passes", ok, str(errs) if not ok else "")

    # Step 3: State store — create record
    print("\nStep 3: State store — create record")
    store = StateStore()
    try:
        state_path = store._path(SMOKE_JOB_ID)
        if state_path.exists():
            state_path.unlink()
        store.create_job_record(job)
        record = store.read_job_record(SMOKE_JOB_ID)
        check("Record created with status=queued", record["status"] == "queued")
        check("Record has 3 tasks",                len(record["tasks"]) == 3)
    except Exception as exc:
        check("State store create", False, str(exc)); traceback.print_exc(); return

    # Step 4: Update to running
    print("\nStep 4: Update status to running")
    try:
        store.update_job_status(SMOKE_JOB_ID, JobStatus.running)
        check("Status updated to running",
              store.read_job_record(SMOKE_JOB_ID)["status"] == "running")
    except Exception as exc:
        check("Status update", False, str(exc)); return

    # Step 5: Supervisor
    print("\nStep 5: Route through Supervisor")
    try:
        result = Supervisor().process(job)
        check("Result status=completed", result.status == JobStatus.completed,
              f"actual={result.status}")
        check("3 task outputs",  len(result.task_outputs) == 3,
              f"got {len(result.task_outputs)}")
        check("No errors",       len(result.errors) == 0)
        check("completed_at set", result.completed_at is not None)
        for out in result.task_outputs:
            check(f"Task {out.task_id} succeeded", out.success is True,
                  out.error_message or "")
    except Exception as exc:
        check("Supervisor.process()", False, str(exc)); traceback.print_exc(); return

    # Step 6: Write final result
    print("\nStep 6: Write final result")
    try:
        store.write_final_result(result)
        record = store.read_job_record(SMOKE_JOB_ID)
        check("Final status=completed",  record["status"] == "completed")
        check("result payload present",  record["result"] is not None)
        check("finalised_at set",        record["finalised_at"] is not None)
    except Exception as exc:
        check("write_final_result", False, str(exc)); return

    # Step 7: JSON round-trip
    print("\nStep 7: JSON round-trip integrity")
    try:
        raw = json.loads(state_path.read_text())
        check("Valid JSON",            isinstance(raw, dict))
        check("job_id round-trips",    raw["job_id"] == SMOKE_JOB_ID)
        check("3 outputs round-trip",  len(raw["result"]["task_outputs"]) == 3)
    except Exception as exc:
        check("JSON round-trip", False, str(exc))


if __name__ == "__main__":
    run()
    passed = sum(1 for _, ok, _ in checks if ok)
    failed = sum(1 for _, ok, _ in checks if not ok)
    total  = len(checks)
    print(f"\n{'='*52}")
    print(f"SMOKE TEST: {passed}/{total} checks passed")
    if failed:
        print("FAILED:")
        for name, ok, detail in checks:
            if not ok:
                print(f"  - {name}" + (f": {detail}" if detail else ""))
    print("RESULT:", "PASS" if failed == 0 else "FAIL")
    print(f"{'='*52}")
    sys.exit(0 if failed == 0 else 1)
