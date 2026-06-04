"""
Pytest test suite for Hermes Multi-Agent Harness v1.

Required tests:
  - valid HarnessJob passes validation
  - invalid HarnessJob is rejected
  - invalid role output is rejected
  - supervisor routes to the correct role
  - failed validation does not write final output
  - atomic write creates valid JSON
  - atomic write does not corrupt existing JSON
  - existing drift diagnostic still runs
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from harness.atomic_io   import atomic_json_read, atomic_json_write
from harness.job_models  import (
    AgentInput, AgentOutput, AuditEvent, HarnessError, HarnessJob, HarnessResult,
    HarnessTask, JobStatus, RoleType, SafetyConfig, ToolCategory,
)
from harness.roles        import ExecutionAgent, MemoryStateAgent, ResearchAgent
from harness.state_store  import StateStore
from harness.supervisor   import Supervisor
from harness.validators   import validate_job, validate_tool_access


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def store(tmp_path):
    return StateStore(state_dir=tmp_path / "state")

@pytest.fixture
def supervisor():
    return Supervisor()

@pytest.fixture
def simple_job():
    return HarnessJob(
        job_id="job-test-001",
        tasks=[HarnessTask(
            task_id="t1",
            role_type=RoleType.research,
            payload={"query": "test"},
        )],
    )


# ── Schema validation ─────────────────────────────────────────────────────

def test_valid_harness_job_passes_validation():
    job = HarnessJob(
        job_id="job-valid-001",
        tasks=[
            HarnessTask(task_id="t1", role_type=RoleType.research,     payload={"query": "q"}),
            HarnessTask(task_id="t2", role_type=RoleType.memory_state, payload={"operation": "read", "key": "k"}),
            HarnessTask(task_id="t3", role_type=RoleType.execution,    payload={"action": "noop"}),
        ],
    )
    assert job.job_id == "job-valid-001"
    assert len(job.tasks) == 3


def test_invalid_harness_job_empty_tasks_is_rejected():
    with pytest.raises(ValidationError) as exc_info:
        HarnessJob(job_id="job-bad", tasks=[])
    assert "tasks" in str(exc_info.value).lower()


def test_invalid_harness_job_blank_job_id_is_rejected():
    with pytest.raises(ValidationError):
        HarnessJob(
            job_id="   ",
            tasks=[HarnessTask(task_id="t1", role_type=RoleType.execution)],
        )


def test_invalid_harness_task_blank_task_id_is_rejected():
    with pytest.raises(ValidationError):
        HarnessTask(task_id="", role_type=RoleType.research)


def test_invalid_agent_output_missing_required_fields_is_rejected():
    with pytest.raises(ValidationError):
        AgentOutput.model_validate({"task_id": "t1"})  # role_type and result missing


# ── Validator helpers ─────────────────────────────────────────────────────

def test_validate_job_accepts_valid_job(simple_job):
    ok, errors = validate_job(simple_job)
    assert ok
    assert errors == []


def test_validate_job_rejects_duplicate_task_ids():
    job = HarnessJob(
        job_id="job-dup",
        tasks=[
            HarnessTask(task_id="same", role_type=RoleType.research, payload={"query": "q"}),
            HarnessTask(task_id="same", role_type=RoleType.execution, payload={"action": "a"}),
        ],
    )
    ok, errors = validate_job(job)
    assert not ok
    assert any("duplicate" in e.lower() for e in errors)


# ── Role tests ────────────────────────────────────────────────────────────

def test_research_agent_returns_stub():
    agent = ResearchAgent()
    out = agent.run(AgentInput(task_id="t1", role_type=RoleType.research, payload={"query": "test"}))
    assert out.success is True
    assert out.role_type == RoleType.research
    assert "STUB" in out.result["findings"]


def test_memory_state_agent_returns_stub():
    agent = MemoryStateAgent()
    out = agent.run(AgentInput(
        task_id="t2", role_type=RoleType.memory_state,
        payload={"operation": "read", "key": "k"},
    ))
    assert out.success is True
    assert "STUB" in out.result["value"]


def test_execution_agent_returns_stub():
    agent = ExecutionAgent()
    out = agent.run(AgentInput(
        task_id="t3", role_type=RoleType.execution,
        payload={"action": "noop"},
    ))
    assert out.success is True
    assert "STUB" in out.result["outcome"]


def test_role_mismatch_returns_failure():
    agent = ExecutionAgent()
    out = agent.run(AgentInput(task_id="t1", role_type=RoleType.research, payload={}))
    assert out.success is False
    assert "mismatch" in (out.error_message or "").lower()


# ── Invalid role output is rejected ───────────────────────────────────────

def test_supervisor_invalid_role_output_is_rejected(supervisor, monkeypatch):
    """A role that raises at runtime produces failed_execution, not a crash."""
    import harness.roles as roles_mod
    def bad_run(self, inp):
        raise RuntimeError("simulated role crash")
    monkeypatch.setattr(roles_mod.ResearchAgent, "run", bad_run)

    job = HarnessJob(
        job_id="job-bad-role",
        tasks=[HarnessTask(task_id="t1", role_type=RoleType.research, payload={"query": "q"})],
    )
    result = supervisor.process(job)
    assert result.status == JobStatus.failed_execution
    assert len(result.errors) == 1
    assert "simulated role crash" in result.errors[0].message


# ── Supervisor routing ─────────────────────────────────────────────────────

def test_supervisor_routes_to_research_role(supervisor, simple_job):
    result = supervisor.process(simple_job)
    assert result.status == JobStatus.completed
    assert result.task_outputs[0].role_type == RoleType.research


def test_supervisor_routes_to_memory_state_role(supervisor):
    job = HarnessJob(
        job_id="job-mem",
        tasks=[HarnessTask(
            task_id="m1", role_type=RoleType.memory_state,
            payload={"operation": "read", "key": "k"},
        )],
    )
    result = supervisor.process(job)
    assert result.status == JobStatus.completed
    assert result.task_outputs[0].role_type == RoleType.memory_state


def test_supervisor_routes_to_execution_role(supervisor):
    job = HarnessJob(
        job_id="job-exec",
        tasks=[HarnessTask(task_id="e1", role_type=RoleType.execution, payload={"action": "noop"})],
    )
    result = supervisor.process(job)
    assert result.status == JobStatus.completed
    assert result.task_outputs[0].role_type == RoleType.execution


def test_supervisor_completed_result_has_completed_at(supervisor, simple_job):
    result = supervisor.process(simple_job)
    assert result.status == JobStatus.completed
    assert result.completed_at is not None


def test_supervisor_failed_validation_has_no_completed_at(supervisor):
    bad_job = HarnessJob.model_construct(job_id="j", tasks=[], metadata={})
    result = supervisor.process(bad_job)
    assert result.status == JobStatus.failed_validation
    assert result.completed_at is None


# ── Failed validation does not write final output ─────────────────────────

def test_failed_validation_does_not_write_final_output(store):
    """
    A failed_validation result written to the store must have
    completed_at=None and no task_outputs.
    """
    good_job = HarnessJob(
        job_id="j-failval",
        tasks=[HarnessTask(task_id="t1", role_type=RoleType.research, payload={"query": "q"})],
    )
    store.create_job_record(good_job)

    failed_result = HarnessResult(
        job_id="j-failval",
        status=JobStatus.failed_validation,
        errors=[HarnessError(job_id="j-failval", error_type="test", message="forced")],
    )
    assert failed_result.completed_at is None

    store.write_final_result(failed_result)
    record = store.read_job_record("j-failval")
    assert record["status"] == JobStatus.failed_validation.value
    assert record["result"]["completed_at"] is None
    assert record["result"]["task_outputs"] == []


# ── State store ───────────────────────────────────────────────────────────

def test_state_store_create_and_read(store, simple_job):
    store.create_job_record(simple_job)
    record = store.read_job_record(simple_job.job_id)
    assert record["job_id"] == simple_job.job_id
    assert record["status"] == JobStatus.queued.value


def test_state_store_update_status(store, simple_job):
    store.create_job_record(simple_job)
    store.update_job_status(simple_job.job_id, JobStatus.running)
    assert store.read_job_record(simple_job.job_id)["status"] == "running"


def test_state_store_append_validation_error(store, simple_job):
    store.create_job_record(simple_job)
    err = HarnessError(job_id=simple_job.job_id, error_type="t", message="oops")
    store.append_validation_error(simple_job.job_id, err)
    record = store.read_job_record(simple_job.job_id)
    assert len(record["validation_errors"]) == 1
    assert record["validation_errors"][0]["message"] == "oops"


def test_state_store_write_and_read_final_result(store, simple_job):
    store.create_job_record(simple_job)
    result = Supervisor().process(simple_job)
    store.write_final_result(result)
    record = store.read_job_record(simple_job.job_id)
    assert record["status"] == JobStatus.completed.value
    assert record["result"] is not None
    assert record["finalised_at"] is not None


def test_state_store_missing_job_raises(store):
    with pytest.raises(FileNotFoundError):
        store.read_job_record("does-not-exist")


# ── Atomic writer ─────────────────────────────────────────────────────────

def test_atomic_write_creates_valid_json(tmp_path):
    target = tmp_path / "out.json"
    atomic_json_write(target, {"hello": "world", "n": 42})
    assert target.exists()
    assert json.loads(target.read_text()) == {"hello": "world", "n": 42}


def test_atomic_write_does_not_corrupt_existing_json(tmp_path):
    target = tmp_path / "data.json"
    atomic_json_write(target, {"v": 1})
    atomic_json_write(target, {"v": 2})
    data = json.loads(target.read_text())
    assert data == {"v": 2}


def test_atomic_write_leaves_no_tmp_files(tmp_path):
    atomic_json_write(tmp_path / "clean.json", {"x": 1})
    assert list(tmp_path.glob("*.tmp.json")) == []


def test_atomic_read_round_trip(tmp_path):
    target = tmp_path / "rt.json"
    payload = {"nested": {"a": 1}, "list": [1, 2, 3]}
    atomic_json_write(target, payload)
    assert atomic_json_read(target) == payload


# ── Existing drift diagnostic regression ─────────────────────────────────

def test_existing_drift_diagnostic_still_runs():
    """
    orchestrator_v2.py must exit 0 and produce valid JSON.
    Config files may be absent; worker.py catches those errors and
    returns defaults, so the orchestrator outputs {} (no drift).
    """
    result = subprocess.run(
        ["/home/jfroh/hermes/harness_venv/bin/python", "/home/jfroh/hermes/harness/orchestrator_v2.py"],
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, (
        f"orchestrator_v2.py exited {result.returncode}\n"
        f"stderr: {result.stderr}\nstdout: {result.stdout}"
    )
    output = json.loads(result.stdout)
    assert isinstance(output, dict)


# ── Guardrail tests ─────────────────────────────────────────────────────────

def test_guardrail_defaults_block_all():
    config = SafetyConfig()
    for category in [ToolCategory.research, ToolCategory.memory, ToolCategory.execution]:
        ok, msg = validate_tool_access(config, RoleType.research, category)
        assert not ok
        assert "Guardrail violation" in msg


def test_guardrail_allowlist_blocks_non_allowlisted():
    config = SafetyConfig(
        deterministic_only=False,
        allow_real_tool_calls=True,
        allowed_tool_categories=[ToolCategory.research],
        require_audit_log=False
    )
    # research allowed
    ok, _ = validate_tool_access(config, RoleType.research, ToolCategory.research)
    assert ok
    # memory not allowed
    ok, msg = validate_tool_access(config, RoleType.research, ToolCategory.memory)
    assert not ok
    assert "not in allowlist" in msg


def test_guardrail_requires_audit_log():
    config = SafetyConfig(
        deterministic_only=False,
        allow_real_tool_calls=True,
        allowed_tool_categories=[ToolCategory.research],
        require_audit_log=True
    )
    # no audit context - blocked
    ok, msg = validate_tool_access(
        config, RoleType.research, ToolCategory.research, has_audit_context=False
    )
    assert not ok
    assert "Audit logging required" in msg
    # with audit context - pass
    ok, _ = validate_tool_access(
        config, RoleType.research, ToolCategory.research, has_audit_context=True
    )
    assert ok


def test_audit_event_model_validates():
    event = AuditEvent(
        event_id="evt-001",
        job_id="job-001",
        task_id="t1",
        role_type=RoleType.research,
        proposed_tool_category=ToolCategory.research,
        action="web_search",
        status="attempted",
        message="Testing audit event"
    )
    assert event.event_id == "evt-001"
    assert isinstance(event.timestamp, datetime)
