# Consolidated PAV Review and Integration Proposal: MVP Research Pipeline

This proposal consolidates the findings from the three completed Produce-Audit-Verify (PAV) loops and outlines an architectural plan for integrating these isolated drivers into a unified, manually-triggered MVP pipeline runner.

## 1. Summary of Completed PAV Loops
The drivers were implemented as read-only, non-persistent, manual-trigger scripts within the `harness` repository.

| Component | Commit Hash | Scope | Status |
| :--- | :--- | :--- | :--- |
| **OpenAI RSS** | `c57843a` | OpenAI News | Verified |
| **Hugging Face RSS** | `7997509` | Blog RSS only | Verified |
| **GitHub Releases** | `17014c7` | 4 Approved Repos | Verified |

## 2. Refactoring & Shared Structure
The current drivers contain redundant logic regarding `urllib` request handling, user-agent injection, XML/JSON parsing, and file I/O.
*   **Recommended Shared Structure:** A `pipeline_core` library (non-persistent, library-only) containing:
    *   `RequestEngine`: Manages headers/User-Agent.
    *   `FetcherBase`: Abstract interface for drivers.
    *   `Logger`: Standardized evidence and audit logging.

## 3. Proposed Integration Plan
### File Layout
```text
research_pipeline/
├── core/               # Shared logic (RequestEngine, FetcherBase)
├── drivers/            # Refactored drivers (OpenAI, HF, GitHub)
├── runner.py           # Orchestrator (manual trigger only)
└── data/               # Output (Evidence Reports, JSON raw)
```

### Proposed Interface & Execution
*   **CLI:** `python3 runner.py --fetch [source|all] --audit` (No scheduling).
*   **Output Format:** Raw data as partitioned `.json` files in `data/raw/`.
*   **Evidence Format:** Standardized Markdown (`audit_report.md`) generated per execution.

### Deduplication & Error Handling
*   **Deduplication:** A simple JSON hash-map (`data/state.json`) comparing unique identifiers (e.g., URL/HTML_URL).
*   **Error Handling:** "Circuit Breaker" pattern: failures are logged in the Evidence Report; the orchestrator continues processing remaining sources.

### Governance & Verification
*   **Plausibility Check:** Placed between data synthesis and report generation. Anomalies (e.g., spikes in item count) trigger a block requiring manual user approval.
*   **Integrated PAV Test Plan:**
    1.  **Unit Tests:** Validate `core` connectivity and parser robustness.
    2.  **Integration Test:** Run `runner.py --audit` on dummy/mock data.
    3.  **Governance Gate:** Manual user review of the Evidence Report before any Telegram/summary output is generated.

## 4. Risks & Governance
*   **Scope Creep:** Risk of transition to automated/persistent execution. *Mitigation:* Explicit check in `runner.py` main-block requiring manual CLI flags.
*   **Fragility:** RSS/HTML sources are inherently brittle. *Mitigation:* Fail-safe parsing logic (None-checks) implemented.

## 5. Recommendation
**PROCEED** with integration design based on this shared-library architecture. The implementation remains **PAUSED** and strictly manual. 

Final status: This proposal is ready for review.
