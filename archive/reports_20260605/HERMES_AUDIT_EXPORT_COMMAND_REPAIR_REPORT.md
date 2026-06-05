# Hermes Audit Export Command Repair Report

## Executive Summary
The export command repair is complete. The nightly audit script now successfully exports projects and regenerates master files for NotebookLM ingestion.

## Current Failure
Failure chain: nightly script -> broken export command (using defunct `python3 -m cli.main`) -> `Personal_OS.md` was not generated -> master files (`2_states_master.txt`, `3_runbooks_master.txt`) remained stale.

## Broken Command
Old Command: `python3 -m cli.main export --project "<name>" --output "<path>"`
Result: Failed to find module `cli.main`.

## Export Entry Points Investigated
- `~/.hermes/hermes-memory/cli/main.py`
- `~/.hermes/hermes-memory/cli/` module imports
- `~/.hermes/scripts/nightly_brain_audit.sh` logic

## Candidate Commands Tested
- `python3 -m cli.main export ...` -> Failed
- `python3 /home/jfroh/.hermes/hermes-memory/cli/main.py export ...` -> Proven successful.

## Proven Working Export Command
`python3 /home/jfroh/.hermes/hermes-memory/cli/main.py export --project "<name>" --output "<path>"`

## Fix Applied
Updated `~/.hermes/scripts/nightly_brain_audit.sh` to explicitly call the absolute path to `hermes-memory/cli/main.py` for all project exports ("Personal OS", "debug", "proper-test").

## Manual Verification Result
Executed `bash ~/.hermes/scripts/nightly_brain_audit.sh`:
Result: Script completed successfully with regenerating master files. (Note: "Operation not permitted" warnings regarding metadata on `/mnt/h/` are expected behavior for cross-filesystem `mv`).

## Master File Timestamp Result
- `/mnt/h/My Drive/Hermes_Workspace/Setup/2_states_master.txt`: 2026-06-05 19:42:49
- `/mnt/h/My Drive/Hermes_Workspace/Setup/3_runbooks_master.txt`: 2026-06-05 19:42:49

## Master File Content Check
(Summary of first 20 lines)
Files contain expected export content, reflecting the current state of brain databases.

## Cron Status
`0 2 * * * /home/jfroh/.hermes/scripts/nightly_brain_audit.sh`

## Files Modified
- `~/.hermes/scripts/nightly_brain_audit.sh`

## Commit / Git Status
Not a git repository.

## Remaining Risks
Cross-filesystem `mv` warnings regarding file metadata are expected but suggest potential issues if file permissions become critical for NotebookLM; currently acceptable.

## Recommended Next Step
Proceed to ChatGPT adjudication of the Multi-Agent Harness.

Audit export command repair investigation complete. Awaiting next instruction.
