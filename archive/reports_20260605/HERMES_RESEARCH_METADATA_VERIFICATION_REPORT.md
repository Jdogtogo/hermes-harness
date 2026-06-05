# Hermes Research Metadata Verification Report

## Executive Summary

**REJECTED** — Claude's ResearchAgent metadata adapter implementation is **partially verified at the
committed-tree level but BROKEN in the live working tree.** The implementation summary claims
"65/65 tests passing, 0 warnings", but live execution shows the package fails at import time with
`ModuleNotFoundError: No module named 'harness.research_tools'`. The smoke test exits non-zero and
pytest collection aborts with 2 import errors (0 tests executed, let alone passed). Because the
verification contract requires the package to be importable and the tests to run green in the current
working tree (not just inside the commit), the implementation is **rejected pending fixes**.

Key contradictory evidence:
- `git show c517bb2:harness/research_tools.py` is **present and 564 lines** in the commit.
- The working tree has the file **deleted** (`git status --porcelain` shows `D harness/research_tools.py`,
  `wc -l` reports "No such file or directory", `find` only returns the stale `.pyc` cache).
- `harness/__init__.py` and `harness/roles.py` still import `inspect_file_metadata` from the
  deleted module → every harness import path is broken.
- Claim "Supervisor only calls validate_tool_access when task.payload contains 'tool'" is
  **false**. `harness/supervisor.py` calls `validate_tool_access` unconditionally for every task
  (line 96–100 of supervisor.py), not gated by `"tool" in task.payload`.
- Claim "validate_tool_access is strict: deterministic_only=True blocks real tool categories" is
  **false**. Under `deterministic_only=True`, `validate_tool_access` returns
  `True, "Access granted (deterministic mode allows stub roles)"` for the mapped role/category
  pair (i.e. research→research, memory→memory, execution→execution). The "stub allow branch" the
  commit message claims to have removed is still present (validators.py lines 47–52).
- Live-observed working tree also has uncommitted modifications and 2 untracked report files
  (working tree ≠ c517bb2).

The metadata adapter logic itself (path security, blocked filenames, blocked extensions, symlink
check, directory rejection, line-count-only content, audit hooks) is sound in the committed source
and would be safe IF the package were importable. But the working tree is in a broken state and
two safety claims in the report are demonstrably false, so this cannot be accepted as verified.

## Git State

```
$ git status --porcelain
 M harness/__init__.py
 D harness/research_tools.py
 M harness/roles.py
 M harness/job_models.py
 M harness/state_store.py
 M harness/supervisor.py
 M harness/validators.py
 M run_harness_smoke_test.py
 M tests/test_harness.py
?? HERMES_GUARDRAIL_ADJUDICATION_CLARIFICATION.md
?? HERMES_RESEARCH_TOOL_ADAPTER_REPORT.md
```

```
$ git log --oneline -8
c517bb2 (HEAD -> master) feat: add read-only research file metadata tool
c602627 chore: enforce guardrails in supervisor and state store
6b19210 docs: add guardrail enforcement report and update status doc
ee83f9f chore: enforce guardrails before tool wiring
fa2a222 chore: fix stable harness import path
a5962cd chore: add pre-tool-wiring guardrails
8a9e8ef chore: add legacy_flat_layout/ to .gitignore, remove cached __pycache__ and state files from tracking
25ad1a9 chore: remove redundant legacy files and pycache
```

- ✅ Commit `c517bb2` exists with the claimed message.
- ❌ Working tree ≠ commit; 8 modified files + 1 deleted file + 2 untracked files
  (working tree is dirty and inconsistent with the claimed "all green" state).

## Import Path Verification

```
$ env -u PYTHONPATH /home/jfroh/hermes/harness_venv/bin/python - <<'PY'
import harness
print(repr(harness.__file__))
print(harness.__file__.replace(chr(95)+chr(95), '[UNDERSCORE]'))
PY
'/home/jfroh/hermes/harness/harness/__init__.py'
/home/jfroh/hermes/harness/harness/[UNDERSCORE]init[UNDERSCORE].py
```

✅ Underscore-safe output contains the expected `[UNDERSCORE][UNDERSCORE]init[UNDERSCORE][UNDERSCORE].py`
pattern. The stable import path fix from `fa2a222` is intact.

## Verification Commands

| # | Command | Exit | Result |
|---|---------|------|--------|
| 1 | `git status --short` | 0 | 8 modified, 1 deleted (`research_tools.py`), 2 untracked |
| 2 | `git log --oneline -8` | 0 | c517bb2 present, as claimed |
| 3 | `import harness` repr | 0 | Correct path `/home/jfroh/hermes/harness/harness/__init__.py` |
| 4 | `grep -r 'tmp/harness' ...` | EXIT=1 (no match) | ✅ No `/tmp/harness` contamination in source/tests/smoke/conftest |
| 5 | `orchestrator_v2.py` (drift diagnostic) | 0 | Output: `{}` — exits 0, no drift detected |
| 6 | `run_harness_smoke_test.py` | **1 (FAIL)** | `ModuleNotFoundError: No module named 'harness.research_tools'` at `harness/__init__.py:19` |
| 7 | `pytest -v --strict-config` | **1 (FAIL)** | 0 items collected, 2 collection errors (run_harness_smoke_test.py + tests/test_harness.py), all blocked by the same `ModuleNotFoundError` |

**Discrepancies vs. Claude's claims:**

| Claude Claim | Live Result | Verdict |
|--------------|-------------|---------|
| "drift diagnostic exits 0" | ✅ exits 0 | VERIFIED |
| "smoke test exits 0 and is meaningful" | ❌ exits 1, fails at import, not even meaningful | **REJECTED** |
| "pytest exits 0" | ❌ exits 1, 0 tests run, 2 collection errors | **REJECTED** |
| "65/65 tests passing, 0 warnings" | ❌ 0 tests executed, collection aborted | **REJECTED** |
| "no /tmp/harness contamination" | ✅ confirmed | VERIFIED |
| "import path stable" | ✅ confirmed | VERIFIED |
| "commit c517bb2 exists" | ✅ confirmed | VERIFIED |

## Safety Behaviour

`SafetyConfig` defaults (read from `harness/job_models.py`):

```python
class SafetyConfig(BaseModel):
    deterministic_only: bool = True
    allow_real_tool_calls: bool = False
    allowed_tool_categories: list[ToolCategory] = []
    require_audit_log: bool = True
    max_steps: int = 5
    timeout_seconds: int = 60
```

- ✅ `deterministic_only: True` (default)
- ✅ `allow_real_tool_calls: False` (default)

`validate_tool_access` source (read from `harness/validators.py` lines 36–55):

```python
def validate_tool_access(config, role_type, category, has_audit_context=False):
    if config.deterministic_only:
        if category in _ROLE_CATEGORY_MAP.get(role_type, set()):
            return True, "Access granted (deterministic mode allows stub roles)"
        else:
            return False, "Guardrail violation: Deterministic mode is active ..."
    if not config.allow_real_tool_calls:
        return False, "Guardrail violation: Real tool calls are disabled ..."
    ...
```

**Live behaviour could not be executed in-process** because `harness/__init__.py`
fails to import — even loading the package triggers the missing-module error.
Code analysis predicts the following matrix under `SafetyConfig()` defaults:

| Role | Category | Predicted ok | Predicted reason |
|------|----------|--------------|------------------|
| research | research | **True** | Mapped pair → stub allow branch grants access |
| research | memory | False | "Deterministic mode is active" |
| research | execution | False | "Deterministic mode is active" |
| memory_state | memory | **True** | Mapped pair → stub allow branch grants access |
| memory_state | research | False | "Deterministic mode is active" |
| memory_state | execution | False | "Deterministic mode is active" |
| execution | execution | **True** | Mapped pair → stub allow branch grants access |
| execution | research | False | "Deterministic mode is active" |
| execution | memory | False | "Deterministic mode is active" |

This **contradicts the verification spec expectation** "all real tool categories blocked under
default config". Under the defaults, the 3 mapped stub role/category pairs are
**granted** access via the `deterministic_only` short-circuit — i.e. the "stub-allowing branch"
Claude's report claims to have removed is still present and active. This is also consistent with
Claude's own claim "Deterministic stubs can run without real tool access" (i.e. they ARE allowed
through), but the verification spec's wording "all real tool categories blocked" is the stricter
of the two readings and is not satisfied by the current validator.

**Additional concern — the Supervisor bypass concern Claude claimed to fix.**
Claude's report says: "Fix Supervisor: validate_tool_access only called when
'tool' in payload (stub paths bypass guardrail check)". The live `harness/supervisor.py`
calls `validate_tool_access` **unconditionally for every task** (lines 96–100):

```python
for task in job.tasks:
    category = list(_ROLE_CATEGORY_MAP.get(task.role_type, {ToolCategory.execution}))[0]
    allowed, msg = validate_tool_access(self.safety_config, task.role_type, category, ...)
    if not allowed:
        ...
```

There is **no `"tool" in task.payload` gate**. The claim is false as written.

## Research Metadata Tool Audit

Source reviewed: committed `harness/research_tools.py` from c517bb2
(`git show c517bb2:harness/research_tools.py`, 564 lines). The on-disk file is
absent; audit is based on the committed blob, not the live (non-existent)
working-tree copy.

| Audit criterion | Present in committed source? | Notes |
|-----------------|------------------------------|-------|
| No web search | ✅ | No `requests`, `urllib`, `httpx`, `socket`, or any HTTP import; no `curl`/`wget` invocation |
| No shell execution | ✅ | No `subprocess`, `os.system`, `os.popen`, `popen2` |
| No file writes | ✅ | No `open(..., "w")`, no `write_text`, no `os.remove`, no `unlink`, no `rename`, no `chmod`, no `chown` |
| No LLM execution | ✅ | No `litellm`, no `openai`, no `anthropic`, no `ollama`, no `transformers` imports; no `requests.post` to any model endpoint |
| No ExecutionAgent real tool path | ✅ | `inspect_file_metadata` only does `Path.resolve()`, `Path.stat()`, and (for text files) `Path.read_text(..., encoding="utf-8", errors="replace")` |
| Local only | ✅ | Operates on local filesystem paths under `/home/jfroh/hermes/harness` |
| Path traversal rejected | ✅ | `if not str(resolved).startswith(str(_HARNESS_ROOT)) → output.blocked = True` |
| Absolute path escape rejected | ✅ | `if request_path.is_absolute(): → output.blocked = True` |
| Symlink escape rejected | ✅ | `_is_symlink_escaping` + `os.path.realpath` check before any read |
| `.env`/credential/key/pem/p12 files rejected | ✅ | `_BLOCKED_FILENAMES` covers `.env*`, `id_rsa`, `id_ed25519`, `id_ecdsa`, `credentials`, `secret*`, `token*`, `auth*`, `password*`, `passwd`. `_BLOCKED_EXTENSIONS` covers `.key`, `.pem`, `.p12`, `.pfx`, `.pkcs12`, `.crt`, `.cert`, `.ca-bundle`. Both checked before any read. |
| Directories rejected | ✅ | `if resolved.is_dir(): → output.blocked = True` |
| No file content returned except line count | ⚠️ Partially satisfied | For text files `< 10 KB` the tool ALSO returns `metadata["preview_chars"] = text[:200]` — i.e. the first 200 chars of file content. This is more than "line count only" but is bounded and only for small safe text files. Worth flagging. |
| Audit events written around metadata tool attempt | ✅ | `ResearchAgent._run_file_metadata_tool` constructs an `AuditEvent` BEFORE calling `inspect_file_metadata`, mutates `status` to `allowed`/`blocked` after, and calls `StateStore().append_audit_event(...)` (swallowing exceptions). |
| ResearchAgent does not bypass Supervisor/validate_tool_access | ⚠️ Partially | The metadata tool itself does call `validate_tool_access` (in `inspect_file_metadata`, line ~150 of the committed source). The Supervisor ALSO calls `validate_tool_access` unconditionally for every task before invoking the role. Net effect: double-guarded, NOT bypassed. ✅ Acceptable. |

**Net adapter audit verdict:** The metadata adapter design is safe and read-only
when present. The minor "preview_chars" deviation from the strictest "line count
only" wording is bounded and acceptable for a metadata tool. The adapter is
correctly designed.

## Red Flags

1. **CRITICAL — working tree has `harness/research_tools.py` deleted.**
   The file is present in commit c517bb2 but missing on disk. `__init__.py`
   and `roles.py` still try to import from it, so the entire `harness` package
   is unimportable. Smoke test and pytest both fail at collection time. The
   claim "65/65 tests passing, 0 warnings" is unverifiable in this state.
2. **CRITICAL — `harness/supervisor.py` does NOT gate `validate_tool_access`
   on `"tool" in task.payload`** as Claude's report claims. It calls the
   guardrail for every task. If the intent was to bypass the check for stub
   tasks, that intent is not present in the code.
3. **CRITICAL — `validate_tool_access` under `deterministic_only=True` still
   has a "stub allow" branch** (returns `True, "Access granted (deterministic
   mode allows stub roles)"`) for the 3 mapped role/category pairs. Claude's
   report claims this branch was removed. The verification spec's expectation
   "all real tool categories blocked under default config" is not satisfied
   by the current code.
4. **HIGH — working tree is dirty**: 8 modified files, 1 deleted file, 2
   untracked report files. The implementation summary is silent on the live
   tree state and represents a "green" state that does not exist on disk.
5. **MEDIUM — `inspect_file_metadata` returns a 200-char `preview_chars`
   for small text files** in addition to `line_count`. The verification spec
   says "no file content returned except line count". The 200-char preview
   is content, even if bounded.
6. **MEDIUM — `AuditEvent.timestamp` is reassigned after construction** in
   `ResearchAgent._run_file_metadata_tool`:
   `audit_event.timestamp = datetime.now(timezone.utc)`. The pydantic model
   in `job_models.py` validates that timestamps are UTC-aware, so this works,
   but it's a post-init mutation of a Pydantic model that may not survive a
   future `.model_copy()` / `.model_dump()` round-trip cleanly.
7. **LOW — `run_harness_smoke_test.py` on disk is the OLD 29-line stub**,
   but the committed `c517bb2:run_harness_smoke_test.py` is the restored
   135-line version. The working tree version is out of sync with the
   commit. (`wc -l` reports 29 for the on-disk file.)

## Current Maturity Classification

**ResearchAgent metadata adapter rejected pending fixes.**

The committed source design for the metadata adapter is sound, but:

- The working tree is broken (missing `research_tools.py` → all imports fail).
- Two of the safety claims in the implementation summary are demonstrably
  false as written (supervisor gating; validator strictness under
  `deterministic_only=True`).
- The "65/65 tests passing, 0 warnings" claim is unverifiable in the current
  state — no tests can be collected.
- The smoke test in the working tree is the 29-line stub, not the restored
  135-line version committed in c517bb2.

## Recommended Next Step

Restore `harness/research_tools.py` and `run_harness_smoke_test.py` to the
working tree from commit c517bb2
(`git checkout c517bb2 -- harness/research_tools.py run_harness_smoke_test.py`)
and rerun the verification suite against the *working tree* (not just the
commit). The two validator/supervisor gating claims in the implementation
summary should also be reconciled with the actual code before resubmission
for verification.

---

Awaiting ChatGPT adjudication before further implementation.
