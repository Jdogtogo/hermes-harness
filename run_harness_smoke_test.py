"""
Hermes Multi-Agent Harness — Smoke Test

End-to-end verification with no LLM calls:
  1. All three stub agents complete successfully.
  2. StateStore round-trip (create → process → write → read).
  3. Metadata tool allowed under permissive SafetyConfig.
  4. Metadata tool blocked under default SafetyConfig.
  5. Path traversal rejected by inspect_file_metadata.
  6. Audit events written for metadata tool requests.
  7. No file content or preview returned by metadata tool.
  8. Drift diagnostic (orchestrator_v2.py) still runs cleanly.

Exit code: 0 on full pass, 1 on any failure.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from harness.job_models import (
    HarnessJob, HarnessTask, JobStatus, RoleType, SafetyConfig, ToolCategory,
    AuditEvent, AuditStatus,
)
from harness.research_tools import inspect_file_metadata
from harness.state_store import StateStore
from harness.supervisor import Supervisor

PASS = "✓"
FAIL = "✗"

def call_metadata(path: str, config: SafetyConfig = None):
    if config is None:
        config = SafetyConfig(deterministic_only=True)
    audit_evt = AuditEvent(
        event_id=str(uuid.uuid4()),
        job_id="smoke",
        task_id="smoke",
        role_type=RoleType.research,
        proposed_tool_category=ToolCategory.research,
        action="test",
        status=AuditStatus.pending,
        message="smoke test",
    )
    return inspect_file_metadata(
        task_id="smoke",
        relative_path=path,
        safety_config=config,
        audit_event=audit_evt,
    )

def check(results: list, name: str, condition: bool, detail: str = "") -> None:
    results.append((name, condition, detail))
    status = PASS if condition else FAIL
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))

def run_section(title: str) -> None:
    print(f"\n[{title}]")

def run_smoke() -> int:
    results: list[tuple[str, bool, str]] = []

    # Section 1: Stub agents complete
    run_section("Stub agents")
    sup_default = Supervisor()
    job_stubs = HarnessJob(
        job_id=f"smoke-stubs-{uuid.uuid4().hex[:8]}",
        tasks=[
            HarnessTask(task_id="r1", role_type=RoleType.research,     payload={"query": "smoke test"}),
            HarnessTask(task_id="m1", role_type=RoleType.memory_state, payload={"operation": "read", "key": "k"}),
            HarnessTask(task_id="e1", role_type=RoleType.execution,    payload={"action": "noop"}),
        ],
    )
    result_stubs = sup_default.process(job_stubs)
    check(results, "research stub completes",      result_stubs.status == JobStatus.completed)
    check(results, "all three stubs complete",     len(result_stubs.task_outputs) == 3)
    check(results, "research stub has STUB text",  "STUB" in result_stubs.task_outputs[0].result.get("findings", ""))
    check(results, "memory stub has STUB text",    "STUB" in result_stubs.task_outputs[1].result.get("value", ""))
    check(results, "execution stub has STUB text", "STUB" in result_stubs.task_outputs[2].result.get("outcome", ""))

    # Section 2: StateStore round-trip
    run_section("StateStore round-trip")
    with tempfile.TemporaryDirectory() as tmpdir:
        store = StateStore(state_dir=Path(tmpdir) / "state")
        job_st = HarnessJob(
            job_id=f"smoke-store-{uuid.uuid4().hex[:8]}",
            tasks=[HarnessTask(task_id="s1", role_type=RoleType.research, payload={"query": "state test"})],
        )
        store.create_job_record(job_st)
        result_st = Supervisor(state_store=store).process(job_st)
        store.write_final_result(result_st)
        record = store.read_job_record(job_st.job_id)
        check(results, "StateStore job created",      record["job_id"] == job_st.job_id)
        check(results, "StateStore status completed", record["status"] == JobStatus.completed.value)
        check(results, "StateStore finalised_at set", record["finalised_at"] is not None)
        check(results, "StateStore result not None",  record["result"] is not None)

    # Section 3: Metadata tool
    run_section("Metadata tool — allowed path")
    permissive_cfg = SafetyConfig(
        deterministic_only=False,
        allow_real_tool_calls=True,
        allowed_tool_categories=[ToolCategory.research],
        require_audit_log=False,
    )
    probe_path = "harness/__init__.py"
    with tempfile.TemporaryDirectory() as tmpdir:
        store_m = StateStore(state_dir=Path(tmpdir) / "state")
        job_m = HarnessJob(
            job_id=f"smoke-meta-{uuid.uuid4().hex[:8]}",
            tasks=[HarnessTask(
                task_id="meta1",
                role_type=RoleType.research,
                payload={"tool": "inspect_file_metadata", "path": probe_path},
            )],
        )
        store_m.create_job_record(job_m)
        result_m = Supervisor(safety_config=permissive_cfg, state_store=store_m).process(job_m)
        check(results, "metadata task completes (permissive)", result_m.status == JobStatus.completed)
        if result_m.task_outputs:
            meta = result_m.task_outputs[0].result
            check(results, "exists=True returned",       meta.get("exists") is True)
            check(results, "size_bytes present",         "size_bytes" in meta)
            check(results, "no content/preview in result",
                  not any(k in meta for k in ("content", "preview", "snippet", "text")))
        else:
            check(results, "metadata task output present", False, str(result_m.errors))
        events = store_m.read_job_audit_events(job_m.job_id)
        actions = {e["action"] for e in events}
        check(results, "audit: attempted event written",  "tool_access_attempted"     in actions)
        check(results, "audit: allowed event written",    "tool_access_allowed"        in actions)
        check(results, "audit: succeeded event written",  "tool_execution_succeeded"   in actions)

    # Section 4: Blocked default
    run_section("Metadata tool — default config blocks")
    with tempfile.TemporaryDirectory() as tmpdir:
        store_b = StateStore(state_dir=Path(tmpdir) / "state")
        job_b = HarnessJob(
            job_id=f"smoke-block-{uuid.uuid4().hex[:8]}",
            tasks=[HarnessTask(
                task_id="block1",
                role_type=RoleType.research,
                payload={"tool": "inspect_file_metadata", "path": "harness/__init__.py"},
            )],
        )
        store_b.create_job_record(job_b)
        result_b = Supervisor(state_store=store_b).process(job_b)
        check(results, "default config blocks metadata tool",
              result_b.status == JobStatus.failed_execution)
        check(results, "error mentions deterministic_only",
              any("deterministic_only" in e.message for e in result_b.errors))
        events_b = {e["action"] for e in store_b.read_job_audit_events(job_b.job_id)}
        check(results, "audit: denied event written", "tool_access_denied" in events_b)

    # Section 5: Path safety
    run_section("Path safety checks")
    check(results, "path traversal rejected", call_metadata("../../etc/passwd")["status"] == "denied")
    check(results, "absolute escape rejected", call_metadata("/etc/passwd")["status"] == "denied")
    check(results, ".env rejected",      call_metadata(".env")["status"] == "denied")
    check(results, ".pem rejected",      call_metadata("cert.pem")["status"] == "denied")
    check(results, "directory rejected", call_metadata("harness")["status"] == "denied")

    # Section 8: Drift diagnostic
    run_section("Drift diagnostic")
    proc = subprocess.run(
        ["/home/jfroh/hermes/harness_venv/bin/python", "/home/jfroh/hermes/harness/orchestrator_v2.py"],
        capture_output=True, text=True, timeout=15,
    )
    check(results, "orchestrator_v2 exits 0", proc.returncode == 0)

    # Summary
    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)
    print(f"\nSmoke test: {passed} passed, {failed} failed")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(run_smoke())
