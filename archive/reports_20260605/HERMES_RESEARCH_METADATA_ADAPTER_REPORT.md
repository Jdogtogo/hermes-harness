# Hermes Research Metadata Adapter Report

## Executive Summary

The first gated read-only ResearchAgent metadata adapter has been implemented on top of the Safe Harness v1 foundation (commit c602627). The implementation adds `inspect_file_metadata` — a path-safe, content-free file metadata tool — and wires it into ResearchAgent behind a multi-layer SafetyConfig gate. All 44 baseline guardrail tests continue to pass; 27 new tests were added for a total of 71 passing. The smoke test was expanded from a 29-line stub to 34 end-to-end checks. Zero warnings. Working tree clean after commit.

---

## Starting Baseline

- **Commit:** `c602627` — *"chore: enforce guardrails in supervisor and state store"*
- **Classification:** Safe Harness v1 foundation with enforced pre-tool-wiring guardrails
- **ResearchAgent state:** deterministic stub only
- **Guardrail tests:** 44/44 passing

---

## Files Changed

| File | Change |
|------|--------|
| `harness/research_tools.py` | **New.** `inspect_file_metadata` tool. |
| `harness/job_models.py` | Added `safety_config: SafetyConfig | None` and `has_audit_context: bool` to `AgentInput` for defence-in-depth. |
| `harness/validators.py` | `deterministic_only=True` now **always** returns False from `validate_tool_access`. Stub execution bypasses the validator (no `"tool"` key in payload). |
| `harness/roles.py` | ResearchAgent dispatches to `_run_metadata_tool()` when payload contains `"tool": "inspect_file_metadata"`. Default stub path unchanged. |
| `harness/supervisor.py` | Tool access validation only runs for tasks with `"tool"` in payload. Three-phase audit events written (attempted → allowed/denied → succeeded/failed). `safety_config` injected into `AgentInput`. |
| `harness/__init__.py` | Added `from harness.research_tools import inspect_file_metadata` to package exports. |
| `run_harness_smoke_test.py` | Expanded from 29-line stub to 34-check end-to-end script. |
| `tests/test_harness.py` | 27 new tests; one existing test updated (`test_deterministic_only_allows_stub_roles` → `test_deterministic_only_blocks_real_tool_access`). |

---

## Research Metadata Tool Behaviour

**Tool:** `inspect_file_metadata(path: str) -> dict`

**Allowed root:** `/home/jfroh/hermes/harness/`

**Allowed outputs only:**
- `status` — `"ok"` or `"denied"`
- `exists` — bool
- `resolved_path` — absolute canonical path
- `size_bytes` — int
- `extension` — lowercase suffix
- `last_modified` — UTC ISO-8601 string
- `line_count` — int (safe text formats ≤ 10 MB only)

**Never returned:** file content, previews, snippets, binary data, first N characters, secrets.

**Rejected inputs:**
- Path traversal (`..` components)
- Absolute paths outside harness root
- Symlinks whose resolved target escapes harness root
- Directories
- `.env`, `.pem`, `.p12`, `.key`, `.pfx`, `.crt`, `.cer`, `.gpg`, `.pgp`, `.der` files
- Filenames matching `credentials`, `secrets`, `id_rsa`, `id_dsa`, `id_ecdsa`, `id_ed25519`
- Filenames matching pattern `secret|credential|password|passwd|token|apikey|api_key|private_key|access_key|authkey`

---

## Safety Gate Behaviour

Gates are evaluated in order at two layers:

### Layer 1 — Supervisor (pre-role)
Only runs for tasks where `"tool"` is present in `task.payload`:

1. `SafetyConfig.deterministic_only=True` → blocked (`validate_tool_access` always returns False)
2. `SafetyConfig.allow_real_tool_calls=False` → blocked
3. Role/category mismatch → blocked
4. `ToolCategory.research` not in `allowed_tool_categories` → blocked
5. `require_audit_log=True` and no `state_store` → blocked

Tasks without `"tool"` in payload run the deterministic stub directly, bypassing `validate_tool_access`.

### Layer 2 — ResearchAgent (defence-in-depth)
`_run_metadata_tool()` independently checks all five conditions above before calling `inspect_file_metadata`. If the supervisor is somehow misconfigured, the role refuses to proceed.

---

## Audit Events

For every task containing `"tool": "inspect_file_metadata"`, three audit events are written to `StateStore`:

| Event action | Status | When |
|---|---|---|
| `tool_access_attempted` | `pending` | Before gate evaluation |
| `tool_access_allowed` or `tool_access_denied` | `allowed` / `blocked` | After `validate_tool_access` |
| `tool_execution_succeeded` or `tool_execution_failed` | `allowed` / `rejected` | After role returns |

Stub executions (no `"tool"` key) write no audit events.

---

## Tests Added

New tests in `tests/test_harness.py`:

**Gate tests (via Supervisor):**
- `test_default_config_blocks_metadata_tool_via_supervisor`
- `test_deterministic_only_true_blocks_metadata_tool_via_supervisor`
- `test_allow_real_tool_calls_false_blocks_metadata_tool_via_supervisor`
- `test_missing_research_allowlist_blocks_metadata_tool_via_supervisor`
- `test_allowed_config_permits_metadata_read`

**validate_tool_access behaviour:**
- `test_deterministic_only_blocks_real_tool_access` (replaces old "allows stub roles" test)
- `test_deterministic_only_blocks_all_categories`
- `test_deterministic_stubs_still_run_without_validate_tool_access`

**Path rejection:**
- `test_path_traversal_rejected`
- `test_absolute_path_escape_rejected`
- `test_symlink_escape_rejected`
- `test_env_file_rejected`
- `test_pem_file_rejected`
- `test_key_file_rejected`
- `test_p12_file_rejected`
- `test_credential_file_rejected`
- `test_directory_rejected`

**Content/mutation guarantees:**
- `test_no_content_key_in_metadata_result`
- `test_no_file_mutation_occurs`
- `test_line_count_is_integer_for_text_file`

**Audit events:**
- `test_audit_events_written_for_allowed_metadata_request`
- `test_audit_events_written_for_denied_metadata_request`

**End-to-end:**
- `test_smoke_test_passes`
- `test_no_tmp_harness_references_in_source`

---

## Verification Commands

All commands executed from `/home/jfroh/hermes/harness/` using `env -u PYTHONPATH` and the stable venv.

```
git status --short
→ ?? only (untracked .md files); no staged or modified files

python -c "import harness; print(repr(harness.__file__)); ..."
→ '/home/jfroh/hermes/harness/harness/__init__.py'

grep -r "tmp/harness" harness/ tests/ run_harness_smoke_test.py conftest.py
→ (no output)

python orchestrator_v2.py
→ {} (exit 0)

python run_harness_smoke_test.py
→ Smoke test: 34 passed, 0 failed — All checks passed. (exit 0)

pytest -v --strict-config
→ 71 passed in 0.89s (exit 0, zero warnings)
```

---

## Git Status

```
commit eb39f2d
feat: add gated read-only research metadata adapter

Working tree: clean (3 untracked .md report files, not staged)
```

---

## Current Maturity Classification

**Safe Harness v1 foundation with first gated read-only ResearchAgent metadata adapter.**

The harness can now execute one real (non-stub) operation — reading structural file metadata — but only when all five SafetyConfig gates are explicitly opened. Default configuration remains fully locked. No LLM execution, no network, no writes.

---

## Remaining Gaps

The following are deliberately out of scope at this maturity level:

- **No web search** — ResearchAgent has no search capabilities
- **No LLM execution** — all roles remain deterministic (stubs or metadata-only)
- **No ExecutionAgent real actions** — ExecutionAgent is still a stub
- **No MemoryStateAgent external store** — MemoryStateAgent is still a stub with no persistence backend
- **No APIs** — no HTTP endpoints, no message queues, no webhooks
- **No Ideas Factory** — Ideas Factory pipeline not started
- **No autonomous multi-phase loop** — Supervisor processes one job at a time with no self-scheduling
- **No LLM-based adjudication** — all decision logic is rule-based

---

## Recommended Next Step

Add a second gated research capability: a **local grep/search tool** (`search_files_by_pattern`) that accepts a regex pattern, searches `.py`/`.md` files under `HARNESS_ROOT`, and returns matching file paths and line numbers — never file content. This would give ResearchAgent meaningful structural discovery without content exposure, and follows the same gate pattern already proven here.

---

*Awaiting ChatGPT adjudication before further implementation.*
