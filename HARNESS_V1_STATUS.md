# Hermes Multi-Agent Harness v1 — Status

## What Exists

### Original files (preserved, unchanged)
| File | Purpose |
|---|---|
| `orchestrator_v2.py` | Asyncio drift diagnostic — reads two Hermes config files, computes drift, outputs JSON patch |
| `worker.py` | Subprocess called by orchestrator — reads a YAML config file, returns JSON |
| `schema.py` | **Updated** — ConfigResult preserved; new Harness v1 models added |

### New files added in v1
| File | Purpose |
|---|---|
| `atomic_writer.py` | Atomic JSON write helper (temp → flush → fsync → os.replace) |
| `roles.py` | ResearchAgent, MemoryStateAgent, ExecutionAgent — deterministic STUB placeholders |
| `supervisor.py` | Accepts HarnessJob, validates, routes tasks to roles, returns HarnessResult |
| `state_store.py` | File-backed JSON state store using atomic writes |
| `test_harness.py` | Pytest suite (schema, roles, supervisor, state store, atomic writer, drift diagnostic) |
| `run_harness_smoke_test.py` | End-to-end smoke test (create job → supervisor → state store → read back) |

### Runtime
| Path | Purpose |
|---|---|
| `/tmp/harness_venv/` | Python 3.12 venv with pydantic 2.x and pytest |
| `/tmp/harness/state/` | JSON state files (one per job, created at runtime) |

---

## What Does NOT Exist Yet

- **Real LLM-backed role implementations** — all three roles (Research, MemoryState, Execution) return STUB results
- **Outlines integration** — no structured LLM output via Outlines
- **Async role execution** — supervisor is synchronous; asyncio concurrency lives only in orchestrator_v2.py
- **Task queuing** — no persistent queue; jobs are processed immediately
- **Inter-role communication** — roles cannot pass data to each other
- **Authentication / secrets integration** — no Hermes gateway or token handling
- **Hermes Telegram/webhook triggers** — harness is not yet wired into the Hermes event pipeline
- **Retry logic** — no per-task retry in the supervisor (orchestrator_v2.py has retries for its own use)
- **Role registry hot-reload** — roles are registered at import time in supervisor.py
- **Outbox / result delivery** — HarnessResult is written to a file; no downstream delivery mechanism

---

## Files Changed

- `schema.py` — replaced (ConfigResult preserved, new models added)
- `atomic_writer.py` — new
- `roles.py` — new
- `supervisor.py` — new
- `state_store.py` — new
- `test_harness.py` — new
- `run_harness_smoke_test.py` — new
- `HARNESS_V1_STATUS.md` — new (this file)

---

## How to Run

### Drift diagnostic (original behaviour)
```bash
/tmp/harness_venv/bin/python /tmp/harness/orchestrator_v2.py
```
Reads two Hermes YAML config files. If either is missing, worker.py catches the error and returns defaults, so the output is `{}` (no drift). This is the correct behaviour when config files are absent.

### Smoke test
```bash
/tmp/harness_venv/bin/python /tmp/harness/run_harness_smoke_test.py
```
Creates a 3-task HarnessJob, routes through supervisor, writes to state store, reads back, prints pass/fail summary.

### Full test suite
```bash
cd /tmp/harness && /tmp/harness_venv/bin/pytest test_harness.py -v
```

---

## Remaining Gaps

1. All role implementations are STUB — they do not call any LLM or external service
2. No Outlines integration
3. No Hermes pipeline integration
4. Supervisor is synchronous — large jobs will block
5. State store has no expiry or cleanup
6. No metrics or observability hooks
