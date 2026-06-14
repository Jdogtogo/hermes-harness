# Execution Governor V0

Deterministic policy enforcement layer for Hermes actions.

## Purpose
Enforce action policy, evidence verification, and scope adherence before any Hermes action.

## Rules
- ALLOW: All policies met.
- BLOCK: Violations or failed evidence.
- ESCALATE: Scope drift or missing pre-action details.
