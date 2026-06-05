# Hermes Dashboard Event Stream Plan

## Executive Summary
This document outlines a structured approach for integrating the Harness v1 baseline (tag: `harness-v1-safe-autoadjudication-baseline`) with the Anti-Gravity CLI dashboard / Personal OS interface via a JSONL event stream. The objective is to increase operational transparency for human operators without compromising the safety and determinism of the harness.

## 1. Event Types
The system will emit the following structured events:
- `phase_started`: Harness phase initiation.
- `verification_started`: Individual check or test suite begins.
- `verification_passed`: Verification success.
- `verification_failed`: Verification failed (contains diagnostic info).
- `adjudication_requested`: Manual/Auto submission to GPT adjudicator.
- `adjudication_approved`: Adjudicator returned 'approved'.
- `adjudication_rejected`: Adjudicator returned 'rejected'/'revise'.
- `manual_gate_waiting`: System paused, awaiting human interaction.
- `phase_completed`: Entire phase finished.
- `phase_blocked`: System halted due to safety or guardrail trigger.

## 2. Event Schema
Every event will be a single-line JSON object:
```json
{
  "event_id": "uuid-v4",
  "timestamp": "ISO8601",
  "phase": "string",
  "status": "enum",
  "severity": "info/warning/error/critical",
  "source": "harness-v1-baseline",
  "git_commit": "437ba92",
  "report_path": "path/to/report.md",
  "adjudication_decision": "string | null",
  "next_action": "string | null",
  "human_required": "boolean"
}
```

## 3. Event Output Locations
All event streams shall be written to:
`/home/jfroh/hermes/harness/events/`
- Streams will be stored as rotating daily files: `events/yyyy-mm-dd.jsonl`

## 4. Relationship to Existing Audit Events
- **StateStore Audit Logs:** Contain high-fidelity, persistent traces for adjudication and safety accountability (required for the Manual-Gated protocol).
- **Dashboard Event Stream:** A "fast-path" for UI rendering, containing high-level lifecycle events. The dashboard should NOT replace the StateStore as the system of record.

## 5. Safety Rules
- **Append-only:** The dashboard consumer must only read sequentially from the end of the file.
- **Data Minimization:** No raw model prompts, credentials, or client financial data are permitted in the stream.
- **Isolation:** The event streamer is a passive listener; it does not block or influence the harness execution path.
- **Read-Only:** The dashboard interface will remain read-only for the initial phases to prevent unintended autonomous actions.

## 6. Implementation Phases
- **Phase 1: Event Schema & Writer:** Implement the `EventWriter` utility to ensure JSONL compliance.
- **Phase 2: Integration:** Instrument the `Supervisor` and `adjudicator_client` to emit events at key lifecycle transitions.
- **Phase 3: Dashboard Consumption:** Develop the dashboard parser to render the events in the Anti-Gravity CLI interface.
- **Phase 4: Manual Launch:** Enable UI-based triggering of verified harness phases.
- **Phase 5: Bounded Automation:** Implement UI-based management of bounded automated loops (after safety validation).

Awaiting ChatGPT adjudication before further implementation.