# Hermes Action Gate V0.2

## Purpose
The Action Gate V0.2 is a deterministic, Python-level policy evaluator designed to serve as the enforcement layer for Hermes Agent operations. It operates as an isolated, dry-run security gate that validates proposed actions against a pre-defined security manifest.

## Current Status
- V0.0, V0.1, V0.2 completed.
- Stable checkpoint: V0.2.
- Test coverage: 38/38 passing test cases.

## What This Does
- Enforces strict security policy on proposed actions.
- Validates inputs against JSON schemas.
- Enforces path-based read/write restrictions (root protections, manifest immutability).
- Denies malformed, ambiguous, or adversarial input.
- Provides granular decision evidence with rule identifiers.

## What This Does Not Do
- This is an isolated dry-run evaluator only.
- It is not connected to live Hermes tools.
- It does not enforce live runtime behaviour yet.

## Architecture
- Dual-Adjudicator: Separation of LLM (advisory) and Python (deterministic enforcement) roles.
- Schema Validation: `jsonschema` used to enforce input contracts.

## Input Files
- Manifest: Policy parameters and permissions.
- Action: Proposed operation details.
- State: Loop tracking (attempts, cycles).

## Output Decisions
- `allow`: Action permitted.
- `deny`: Action blocked.
- `require_human`: Action blocked, requires human intervention.
- `lock_task`: System state inconsistent; safety lock engaged.

## Enforcement Rules
- Read-root enforcement (default-deny on secrets/SSH/etc).
- Manifest immutability (`manifest_locked`, `manifest_phase`).
- Loop limits (safety against infinite recursion).
- Schema validation (fail-closed on malformed input).

## Test Suite
- 38 total test cases:
  - V0: Basic logic.
  - V0.1: Path enforcement, manifest immutability.
  - V0.2: Schema validation, malformed input hardening.

## How To Run Tests
```bash
cd /home/jfroh/hermes/harness/action_gate_v0
python3 run_tests.py
```

## Known Limitations
- Manifest immutability is enforced logically via policy, not OS-level filesystem locks.
- Isolated dry-run mode (not wired into runtime).

## Future Integration Requirements
- Static analysis pipeline integration.
- Live tool-interception capability development.

## Safety Boundary
- Restricted to `/home/jfroh/hermes/harness/action_gate_v0/`.
- No live runtime modifications.
