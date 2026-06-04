# Hermes Guardrail Enforcement Report

## Executive Summary

Guardrail enforcement hardening succeeded. All required guardrails are now enforced by Supervisor, validators, and StateStore. All 56 tests pass, drift diagnostic and smoke test continue to work.

## Import Path Verification

- `harness.__file__`: `/home/jfroh/hermes/harness/harness/__init__.py`
- `harness.validators.__file__`: `/home/jfroh/hermes/harness/harness/validators.py`
- Both resolve from the stable path `/home/jfroh/hermes/harness/` — no `/tmp/harness` contamination.

## Files Changed

| File | Why Changed |
|---|---|
| `harness/job_models.py` | Added `AuditStatus` typed enum; fixed `AuditEvent.timestamp` to UTC-aware; changed `status` field from `str` to `AuditStatus`; added validator rejecting naive timestamps |
| `harness/validators.py` | Added explicit `_ROLE_CATEGORY_MAP` enforcing role/category mapping (research→research, memory_state→memory, execution→execution); `validate_tool_access` now uses `role_type` parameter |
| `harness/supervisor.py` | `Supervisor.__init__` now accepts optional `SafetyConfig` (conservative defaults used if omitted); enforces `max_steps` guardrail before execution; rejects task payload and job metadata containing `safety_config` |
| `harness/state_store.py` | Changed `append_audit_event` to accept `(job_id, event)` and write per-job `audit_events` list with atomic writes; `create_job_record` raises `StateStoreError` on duplicate job_id; `_load` wraps `JSONDecodeError` as `StateStoreError` |
| `harness/roles.py` | Updated `AuditEvent.status` assignments to use `AuditStatus` enum; updated `append_audit_event` call signature |
| `harness/__init__.py` | Exports `AuditStatus` and `StateStoreError` |
| `tests/test_harness.py` | Added 24 new tests for guardrail enforcement, role/category mapping, audit event hardening, state store audit events, overwrite protection, corrupted JSON handling, and existing regression tests |
| `HARNESS_V1_STATUS.md` | Updated to reflect guardrails enforced by Supervisor and validators, audit events persistable through StateStore |

## Guardrails Now Enforced

- **Supervisor** enforces `SafetyConfig` defaults (deterministic_only=True, allow_real_tool_calls=False, max_steps=5, etc.)
- Jobs exceeding `max_steps` are rejected before execution with `failed_validation`
- Task payload cannot contain `safety_config` — rejected as override attempt
- Job metadata cannot contain `safety_config` — rejected as override attempt
- `validate_tool_access` enforces role-type mapping: research→research, memory_state→memory, execution→execution
- `deterministic_only=True` blocks all tool categories
- `allow_real_tool_calls=False` blocks even with allowlist
- Audit event timestamp must be UTC-aware (naive timestamps rejected by Pydantic validator)
- Audit event status is typed `AuditStatus` enum (pending/allowed/blocked/rejected), not arbitrary string
- StateStore appends audit events per-job, preserving order, using atomic writes
- `create_job_record` does not silently overwrite existing job files — raises `StateStoreError`
- Corrupted JSON files raise a clean `StateStoreError` not raw exceptions

## Tests Added

| Test | What it validates |
|---|---|
| `test_supervisor_uses_safe_default_safety_config` | Supervisor() uses conservative defaults |
| `test_supervisor_rejects_jobs_exceeding_max_steps` | max_steps enforced before execution |
| `test_supervisor_accepts_jobs_at_max_steps` | Jobs at exactly max_steps pass |
| `test_task_payload_cannot_bypass_safety_config` | task payload override rejected |
| `test_job_metadata_cannot_bypass_safety_config` | job metadata override rejected |
| `test_validate_tool_access_enforces_role_type_mapping_research` | research→memory blocked |
| `test_validate_tool_access_enforces_role_type_mapping_memory` | memory_state→research blocked |
| `test_validate_tool_access_enforces_role_type_mapping_execution` | execution→memory blocked |
| `test_validate_tool_access_valid_role_category_pair` | research→research allowed |
| `test_allow_real_tool_calls_false_blocks_even_with_allowlist` | blocks with allowlist |
| `test_deterministic_only_blocks_all_categories` | every category blocked |
| `test_audit_event_timestamp_is_utc_aware` | timestamp UTC-aware |
| `test_audit_event_rejects_naive_timestamp` | naive timestamp rejected |
| `test_audit_event_status_is_typed` | status is AuditStatus enum |
| `test_state_store_appends_audit_events` | events appended to job record |
| `test_multiple_audit_events_preserve_order` | ordering preserved |
| `test_create_job_record_does_not_silently_overwrite` | duplicate job_id raises error |
| `test_corrupted_json_raises_clean_error` | corrupted JSON raises StateStoreError |
| `test_existing_smoke_test_still_runs` | smoke test exits 0 |

Total: 56 tests (32 original + 24 new)

## Verification Commands

### `import harness`
- command: `cd /home/jfroh/hermes/harness && env -u PYTHONPATH /home/jfroh/hermes/harness_venv/bin/python -c "import harness; print(harness.__file__)"`
- exit status: 0
- output: `/home/jfroh/hermes/harness/harness/__init__.py`

### `import harness.validators`
- command: `cd /home/jfroh/hermes/harness && env -u PYTHONPATH /home/jfroh/hermes/harness_venv/bin/python -c "import harness.validators as v; print(v.__file__); print('validate_job' in dir(v)); print('validate_tool_access' in dir(v))"`
- exit status: 0
- output: `/home/jfroh/hermes/harness/harness/validators.py`, True, True

### Drift diagnostic
- command: `cd /home/jfroh/hermes/harness && env -u PYTHONPATH /home/jfroh/hermes/harness_venv/bin/python /home/jfroh/hermes/harness/orchestrator_v2.py`
- exit status: 0
- output: `{}`

### Smoke test
- command: `cd /home/jfroh/hermes/harness && env -u PYTHONPATH /home/jfroh/hermes/harness_venv/bin/python /home/jfroh/hermes/harness/run_harness_smoke_test.py`
- exit status: 0
- output: (no output — silent success)

### pytest
- command: `cd /home/jfroh/hermes/harness && env -u PYTHONPATH /home/jfroh/hermes/harness_venv/bin/pytest`
- exit status: 0
- output: 56 passed in 0.49s

## Git Status

Commit created: `chore: enforce guardrails before tool wiring`

## Current Maturity Classification

"Safe Harness v1 foundation with enforced pre-tool-wiring guardrails."

## Remaining Gaps

- no real Hermes tool calls yet
- no LLM execution yet
- no Ideas Factory frontend yet
- no API endpoints yet
- no production pipeline integration yet

## Recommended Next Step

Wire the first guarded Hermes tool (read-only file metadata) through the Supervisor with full SafetyConfig validation.

---

Awaiting ChatGPT adjudication before further implementation.
