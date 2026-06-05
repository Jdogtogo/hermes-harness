# Hermes Dashboard Phase 4 Plan

## Current Accepted Maturity
"Safe Harness v1 with read-only dashboard event consumer."

## Current Accepted Commit
b5e8477 -- chore: finalize phase 3 cleanup status

## Goal
Create a small implementation plan for a local read-only dashboard prototype that consumes the event summary produced by harness.event_consumer.

## 1. Candidate Dashboard Forms
- **Simple CLI/TUI**: A terminal-based interface using curses or rich to display event summaries.
- **Static HTML generated from JSON**: A script that reads the event summary and writes a static HTML file for local viewing.
- **Lightweight local web dashboard**: A minimal Flask or FastAPI server serving a single page that polls the event summary.
- **Anti-Gravity CLI integration**: Leveraging the existing Anti-Gravity CLI to display dashboard panels.

## 2. Recommended First Implementation
**Static HTML generated from JSON** is the safest, smallest option:
- No runtime dependencies beyond Python standard library.
- No network exposure; file can be opened in any browser.
- Read-only by design; no server state.
- Easy to audit and verify.

## 3. Data Source
- Primary: `events/harness_events.jsonl` (raw event log)
- Secondary: Output of `harness.event_consumer` (summary JSON or text)

## 4. Display Sections
- Current harness status (running/idle, last check timestamp)
- Latest phase (current phase number/name from event stream)
- Latest adjudication decision (pending, approved, rejected, with timestamp)
- Human required yes/no (flag indicating if manual intervention is needed)
- Event counts by type (verification_started, manual_gate_waiting, etc.)
- Severity counts (info, warning, error, critical)
- Last 10 events (timestamp, type, summary)
- Current git commit/tag if available (from repo harness/)

## 5. Safety Rules
- Read-only only: no writes to event log, no config changes.
- No launch buttons yet (avoid triggering actions).
- No config changes (gateway.strict remains untouched).
- No raw prompts (no LLM interaction).
- No secrets or client financial data displayed.
- No model calls (no inference).
- No task execution (dashboard is purely observational).

## 6. Implementation Phases
- **Phase 4A**: Static HTML report generator script that reads `harness.event_consumer` summary (or parses JSONL) and writes `dashboard/report.html`. Includes auto-refresh via meta-refresh or simple polling via JavaScript.
- **Phase 4B**: Refreshable local dashboard: enhance the static HTML with JavaScript to periodically fetch updated summary (e.g., every 10 seconds) without full reload.
- **Phase 4C**: Manual launch buttons later: add non-functional placeholder buttons for future phased rollout (disabled by default).
- **Phase 4D**: Bounded controls later: after adjudication, enable safe, read-only controls (e.g., pause/resume event generation) with strict validation.

## Next Step
Awaiting ChatGPT adjudication before further implementation.