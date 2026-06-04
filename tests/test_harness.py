"""
Pytest test suite for Hermes Multi-Agent Harness v1.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from harness.atomic_io   import atomic_json_read, atomic_json_write
from harness.job_models  import (
    AgentInput, AgentOutput, AuditEvent, AuditStatus, HarnessError,
    HarnessJob, HarnessResult, HarnessTask, JobStatus, RoleType,
    SafetyConfig, ToolCategory,
)
from harness.research_tools import HARNESS_ROOT, inspect_file_metadata
from harness.roles        import ExecutionAgent, MemoryStateAgent, ResearchAgent
from harness.state_store  import StateStore, StateStoreError
from harness.supervisor   import Supervisor
from harness.validators   import validate_job, validate_tool_access, _ROLE_CATEGORY_MAP


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

@pytest.fixture
def permissive_config():
    return SafetyConfig(
        deterministic_only=False,
        allow_real_tool_calls=True,
        allowed_tool_categories=[ToolCategory.research],
        require_audit_log=False,
    )

@pytest.fixture
def permissive_supervisor(permissive_config, store):
    return Supervisor(safety_config=permissive_config, state_store=store)


# ---- Schema validation -------------------------------------------------

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
        AgentOutput.model_validate({"task_id": "t1"})


# ---- Validator helpers -------------------------------------------------

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


# ---- Role tests --------------------------------------------------------

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


# ---- Invalid role output is rejected -----------------------------------

def test_supervisor_invalid_role_output_is_rejected(supervisor, monkeypatch):
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


# ---- Supervisor routing ------------------------------------------------

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


# ---- Failed validation does not write final output ----------------------

def test_failed_validation_does_not_write_final_output(store):
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


# ---- State store -------------------------------------------------------

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
    result = Supervisor(state_store=store).process(simple_job)
    store.write_final_result(result)
    record = store.read_job_record(simple_job.job_id)
    assert record["status"] == JobStatus.completed.value
    assert record["result"] is not None
    assert record["finalised_at"] is not None


def test_state_store_missing_job_raises(store):
    with pytest.raises(FileNotFoundError):
        store.read_job_record("does-not-exist")


# ---- Atomic writer -----------------------------------------------------

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


# ---- Existing drift diagnostic regression ------------------------------

def test_existing_drift_diagnostic_still_runs():
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


# ---- Guardrail / Safety tests ------------------------------------------

def test_default_safety_config_blocks_all_real_tool_calls():
    config = SafetyConfig()
    assert config.deterministic_only is True
    assert config.allow_real_tool_calls is False
    assert config.allowed_tool_categories == []
    assert config.require_audit_log is True


def test_deterministic_only_blocks_real_tool_access():
    """validate_tool_access always blocks when deterministic_only=True."""
    config = SafetyConfig(deterministic_only=True)
    allowed, msg = validate_tool_access(config, RoleType.research, ToolCategory.research)
    assert allowed is False
    assert "deterministic_only" in msg.lower()


def test_deterministic_only_blocks_all_categories():
    config = SafetyConfig(deterministic_only=True)
    for cat in ToolCategory:
        allowed, msg = validate_tool_access(config, RoleType.research, cat)
        assert allowed is False, f"Expected block for {cat}"
        assert "deterministic_only" in msg.lower()


def test_deterministic_stubs_still_run_without_validate_tool_access(supervisor):
    """Stub tasks do NOT have 'tool' in payload; supervisor skips validate_tool_access."""
    job = HarnessJob(
        job_id="job-stub-pass",
        tasks=[HarnessTask(task_id="t1", role_type=RoleType.research, payload={"query": "q"})],
    )
    result = supervisor.process(job)
    assert result.status == JobStatus.completed
    assert "STUB" in result.task_outputs[0].result["findings"]


def test_allow_real_tool_calls_false_blocks_tool_access():
    config = SafetyConfig(deterministic_only=False, allow_real_tool_calls=False)
    allowed, msg = validate_tool_access(config, RoleType.research, ToolCategory.research)
    assert allowed is False
    assert "allow_real_tool_calls" in msg.lower()


def test_non_allowlisted_category_is_rejected():
    config = SafetyConfig(
        deterministic_only=False,
        allow_real_tool_calls=True,
        allowed_tool_categories=[ToolCategory.execution],
    )
    allowed, msg = validate_tool_access(config, RoleType.research, ToolCategory.research)
    assert allowed is False
    assert "not in allowlist" in msg.lower()


def test_allowlisted_category_passes_when_all_flags_permit():
    config = SafetyConfig(
        deterministic_only=False,
        allow_real_tool_calls=True,
        allowed_tool_categories=[ToolCategory.research],
        require_audit_log=False,
    )
    allowed, msg = validate_tool_access(config, RoleType.research, ToolCategory.research, has_audit_context=False)
    assert allowed is True
    assert msg == "Access granted"


def test_missing_audit_context_rejected_when_required():
    config = SafetyConfig(
        deterministic_only=False,
        allow_real_tool_calls=True,
        allowed_tool_categories=[ToolCategory.memory],
        require_audit_log=True,
    )
    allowed, msg = validate_tool_access(config, RoleType.memory_state, ToolCategory.memory, has_audit_context=False)
    assert allowed is False
    assert "audit" in msg.lower()


def test_audit_context_present_when_required():
    config = SafetyConfig(
        deterministic_only=False,
        allow_real_tool_calls=True,
        allowed_tool_categories=[ToolCategory.memory],
        require_audit_log=True,
    )
    allowed, msg = validate_tool_access(config, RoleType.memory_state, ToolCategory.memory, has_audit_context=True)
    assert allowed is True
    assert msg == "Access granted"


def test_audit_event_model_validates():
    event = AuditEvent(
        event_id="evt-001",
        job_id="job-g-001",
        task_id="t1",
        role_type=RoleType.research,
        proposed_tool_category=ToolCategory.research,
        action="proposed_tool_call",
        status=AuditStatus.blocked,
        message="Blocked by guardrail: deterministic_only=True",
    )
    assert event.event_id == "evt-001"
    assert event.status == AuditStatus.blocked
    assert event.timestamp.tzinfo is not None
    assert event.timestamp.tzinfo == timezone.utc
    event_no_tool = AuditEvent(
        event_id="evt-002",
        job_id="job-g-002",
        task_id="t2",
        role_type=RoleType.execution,
        proposed_tool_category=None,
        action="noop",
        status=AuditStatus.allowed,
        message="No tool proposed",
    )
    assert event_no_tool.proposed_tool_category is None


def test_safety_config_custom_values():
    config = SafetyConfig(
        deterministic_only=False,
        allow_real_tool_calls=True,
        allowed_tool_categories=[ToolCategory.research, ToolCategory.execution],
        require_audit_log=False,
        max_steps=10,
        timeout_seconds=120,
    )
    assert config.deterministic_only is False
    assert config.allow_real_tool_calls is True
    assert len(config.allowed_tool_categories) == 2
    assert config.max_steps == 10
    assert config.timeout_seconds == 120


# ---- Supervisor SafetyConfig enforcement -------------------------------

def test_supervisor_uses_safe_default_safety_config():
    sup = Supervisor()
    assert sup.safety_config.deterministic_only is True
    assert sup.safety_config.allow_real_tool_calls is False
    assert sup.safety_config.max_steps == 5


def test_supervisor_rejects_jobs_exceeding_max_steps():
    sup = Supervisor(safety_config=SafetyConfig(max_steps=2))
    job = HarnessJob(
        job_id="job-too-many",
        tasks=[
            HarnessTask(task_id="t1", role_type=RoleType.research, payload={"query": "q"}),
            HarnessTask(task_id="t2", role_type=RoleType.research, payload={"query": "q"}),
            HarnessTask(task_id="t3", role_type=RoleType.research, payload={"query": "q"}),
        ],
    )
    result = sup.process(job)
    assert result.status == JobStatus.failed_validation
    assert any("max_steps" in e.message for e in result.errors)


def test_supervisor_accepts_jobs_at_max_steps():
    sup = Supervisor(safety_config=SafetyConfig(max_steps=2))
    job = HarnessJob(
        job_id="job-at-limit",
        tasks=[
            HarnessTask(task_id="t1", role_type=RoleType.research, payload={"query": "q"}),
            HarnessTask(task_id="t2", role_type=RoleType.research, payload={"query": "q2"}),
        ],
    )
    result = sup.process(job)
    assert result.status == JobStatus.completed


def test_task_payload_cannot_bypass_safety_config():
    sup = Supervisor()
    job = HarnessJob(
        job_id="job-bypass-payload",
        tasks=[HarnessTask(
            task_id="t1",
            role_type=RoleType.research,
            payload={"query": "q", "safety_config": {"allow_real_tool_calls": True}},
        )],
    )
    result = sup.process(job)
    assert result.status == JobStatus.failed_validation
    assert any("safety_config_override_attempt" in e.error_type for e in result.errors)


def test_job_metadata_cannot_bypass_safety_config():
    sup = Supervisor()
    job = HarnessJob(
        job_id="job-bypass-meta",
        metadata={"safety_config": {"allow_real_tool_calls": True}},
        tasks=[HarnessTask(task_id="t1", role_type=RoleType.research, payload={"query": "q"})],
    )
    result = sup.process(job)
    assert result.status == JobStatus.failed_validation
    assert any("safety_config_override_attempt" in e.error_type for e in result.errors)


# ---- validate_tool_access role/category mapping ------------------------

def test_validate_tool_access_enforces_role_type_mapping_research():
    config = SafetyConfig(
        deterministic_only=False,
        allow_real_tool_calls=True,
        allowed_tool_categories=[ToolCategory.research, ToolCategory.memory, ToolCategory.execution],
        require_audit_log=False,
    )
    allowed, msg = validate_tool_access(config, RoleType.research, ToolCategory.memory)
    assert allowed is False
    assert "not allowed to request" in msg.lower()


# ---- Metadata tool safety gates ----------------------------------------

def test_default_config_blocks_metadata_tool_via_supervisor(store):
    """Default SafetyConfig (deterministic_only=True) must block metadata tool requests."""
    job = HarnessJob(
        job_id=f"job-meta-default-{uuid.uuid4().hex[:8]}",
        tasks=[HarnessTask(
            task_id="t1",
            role_type=RoleType.research,
            payload={"tool": "inspect_file_metadata", "path": "harness/__init__.py"},
        )],
    )
    store.create_job_record(job)
    sup = Supervisor(state_store=store)  # default: deterministic_only=True
    result = sup.process(job)
    assert result.status == JobStatus.failed_execution
    assert any("deterministic_only" in e.message for e in result.errors)


def test_deterministic_only_true_blocks_metadata_tool_via_supervisor(store):
    cfg = SafetyConfig(deterministic_only=True)
    job = HarnessJob(
        job_id=f"job-det-only-{uuid.uuid4().hex[:8]}",
        tasks=[HarnessTask(
            task_id="t1", role_type=RoleType.research,
            payload={"tool": "inspect_file_metadata", "path": "harness/__init__.py"},
        )],
    )
    store.create_job_record(job)
    result = Supervisor(safety_config=cfg, state_store=store).process(job)
    assert result.status == JobStatus.failed_execution
    assert any("deterministic_only" in e.message for e in result.errors)


def test_allow_real_tool_calls_false_blocks_metadata_tool_via_supervisor(store):
    cfg = SafetyConfig(
        deterministic_only=False,
        allow_real_tool_calls=False,
        allowed_tool_categories=[ToolCategory.research],
    )
    job = HarnessJob(
        job_id=f"job-no-real-{uuid.uuid4().hex[:8]}",
        tasks=[HarnessTask(
            task_id="t1", role_type=RoleType.research,
            payload={"tool": "inspect_file_metadata", "path": "harness/__init__.py"},
        )],
    )
    store.create_job_record(job)
    result = Supervisor(safety_config=cfg, state_store=store).process(job)
    assert result.status == JobStatus.failed_execution
    assert any("allow_real_tool_calls" in e.message for e in result.errors)


def test_missing_research_allowlist_blocks_metadata_tool_via_supervisor(store):
    cfg = SafetyConfig(
        deterministic_only=False,
        allow_real_tool_calls=True,
        allowed_tool_categories=[],  # research not in list
        require_audit_log=False,
    )
    job = HarnessJob(
        job_id=f"job-no-cat-{uuid.uuid4().hex[:8]}",
        tasks=[HarnessTask(
            task_id="t1", role_type=RoleType.research,
            payload={"tool": "inspect_file_metadata", "path": "harness/__init__.py"},
        )],
    )
    store.create_job_record(job)
    result = Supervisor(safety_config=cfg, state_store=store).process(job)
    assert result.status == JobStatus.failed_execution
    assert any("allowlist" in e.message for e in result.errors)


def test_allowed_config_permits_metadata_read(store, permissive_config):
    # Use a known file inside HARNESS_ROOT — metadata only, no content returned.
    job = HarnessJob(
        job_id=f"job-meta-ok-{uuid.uuid4().hex[:8]}",
        tasks=[HarnessTask(
            task_id="t1", role_type=RoleType.research,
            payload={"tool": "inspect_file_metadata", "path": "harness/__init__.py"},
        )],
    )
    store.create_job_record(job)
    result = Supervisor(safety_config=permissive_config, state_store=store).process(job)
    assert result.status == JobStatus.completed
    meta = result.task_outputs[0].result
    assert meta["exists"] is True
    assert "size_bytes" in meta
    assert "extension" in meta
    assert "last_modified" in meta


# ---- inspect_file_metadata path rejection tests ------------------------

def test_path_traversal_rejected():
    result = inspect_file_metadata("../../etc/passwd")
    assert result["status"] == "denied"
    assert "traversal" in result.get("reason", "").lower()


def test_absolute_path_escape_rejected():
    result = inspect_file_metadata("/etc/passwd")
    assert result["status"] == "denied"
    assert "harness root" in result.get("reason", "").lower()


def test_symlink_escape_rejected(tmp_path):
    """Symlink pointing outside harness root must be rejected after resolution."""
    target_outside = tmp_path / "outside.txt"
    target_outside.write_text("secret", encoding="utf-8")
    link_inside = HARNESS_ROOT / "symlink_test_escape.lnk"
    try:
        link_inside.symlink_to(target_outside)
        result = inspect_file_metadata("symlink_test_escape.lnk")
        assert result["status"] == "denied"
        assert "root" in result.get("reason", "").lower()
    finally:
        if link_inside.exists() or link_inside.is_symlink():
            link_inside.unlink(missing_ok=True)


def test_env_file_rejected():
    result = inspect_file_metadata(".env")
    assert result["status"] == "denied"


def test_pem_file_rejected():
    result = inspect_file_metadata("server.pem")
    assert result["status"] == "denied"


def test_key_file_rejected():
    result = inspect_file_metadata("id_rsa.key")
    assert result["status"] == "denied"


def test_p12_file_rejected():
    result = inspect_file_metadata("cert.p12")
    assert result["status"] == "denied"


def test_credential_file_rejected():
    result = inspect_file_metadata("credentials.json")
    assert result["status"] == "denied"


def test_directory_rejected():
    result = inspect_file_metadata("harness")
    assert result["status"] == "denied"
    assert "director" in result.get("reason", "").lower()


# ---- No content returned -----------------------------------------------

def test_no_content_key_in_metadata_result():
    result = inspect_file_metadata("harness/__init__.py")
    forbidden = {"content", "preview", "snippet", "text", "first_bytes", "data", "lines"}
    assert result["status"] == "ok"
    assert result.get("exists") is True
    overlap = set(result.keys()) & forbidden
    assert overlap == set(), f"Forbidden keys present: {overlap}"


def test_no_file_mutation_occurs(tmp_path):
    canary = tmp_path / "canary.txt"
    canary.write_text("untouched", encoding="utf-8")
    # File is outside harness root — must be rejected, canary must be unchanged
    result = inspect_file_metadata(str(canary))
    assert result["status"] == "denied"
    assert canary.read_text() == "untouched"


def test_line_count_is_integer_for_text_file():
    result = inspect_file_metadata("harness/__init__.py")
    assert result.get("exists") is True
    lc = result.get("line_count")
    assert isinstance(lc, int) and lc > 0


# ---- Audit events written for metadata tool ----------------------------

def test_audit_events_written_for_allowed_metadata_request(store, permissive_config):
    job = HarnessJob(
        job_id=f"job-audit-ok-{uuid.uuid4().hex[:8]}",
        tasks=[HarnessTask(
            task_id="t1", role_type=RoleType.research,
            payload={"tool": "inspect_file_metadata", "path": "harness/__init__.py"},
        )],
    )
    store.create_job_record(job)
    Supervisor(safety_config=permissive_config, state_store=store).process(job)

    events = store.read_job_audit_events(job.job_id)
    actions = {e["action"] for e in events}
    assert "tool_access_attempted" in actions
    assert "tool_access_allowed"   in actions
    assert "tool_execution_succeeded" in actions


def test_audit_events_written_for_denied_metadata_request(store):
    job = HarnessJob(
        job_id=f"job-audit-deny-{uuid.uuid4().hex[:8]}",
        tasks=[HarnessTask(
            task_id="t1", role_type=RoleType.research,
            payload={"tool": "inspect_file_metadata", "path": "harness/__init__.py"},
        )],
    )
    store.create_job_record(job)
    Supervisor(state_store=store).process(job)  # default: deterministic_only=True

    events = store.read_job_audit_events(job.job_id)
    actions = {e["action"] for e in events}
    assert "tool_access_attempted" in actions
    assert "tool_access_denied"    in actions


# ---- Smoke test passes -------------------------------------------------

def test_smoke_test_passes():
    result = subprocess.run(
        ["/home/jfroh/hermes/harness_venv/bin/python",
         "/home/jfroh/hermes/harness/run_harness_smoke_test.py"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, (
        f"Smoke test exited {result.returncode}\n"
        f"stdout: {result.stdout[-1000:]}\nstderr: {result.stderr[-500:]}"
    )


# ---- Banned path references --------------------------------------------

def test_no_tmp_harness_references_in_source():
    """Confirm the banned stale path does not appear in source, tests, smoke test, or conftest."""
    root = Path("/home/jfroh/hermes/harness")
    search_paths = [
        root / "harness",
        root / "tests",
        root / "run_harness_smoke_test.py",
        root / "conftest.py",
    ]
    # Build the banned pattern dynamically to avoid the test file matching itself.
    banned = "/tmp" + "/harness"
    found = []
    for sp in search_paths:
        if sp.is_dir():
            for f in sp.rglob("*.py"):
                if f == Path(__file__):
                    continue  # skip this file — it contains the pattern by necessity
                text = f.read_text(encoding="utf-8", errors="ignore")
                if banned in text:
                    found.append(str(f))
        elif sp.is_file():
            if Path(sp) == Path(__file__):
                continue
            text = sp.read_text(encoding="utf-8", errors="ignore")
            if banned in text:
                found.append(str(sp))
    assert found == [], f"Banned path found in: {found}"
