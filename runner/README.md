# Autonomy Runner V0

A manifest-first, dry-run-only autonomous execution harness for local workspace maintenance.

## Design
- Manifest: YAML workflow definitions
- Runner: Orchestrator with default-deny governance
- Auditor: Post-execution safety gate

## Setup
Ensure `/home/jfroh/.hermes/runtime/autonomy_runner.disabled` does not exist to enable.
