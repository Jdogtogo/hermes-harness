# HERMES_NOTEBOOKLM_SOURCE_REGISTER.md

## Executive Summary
This document defines the authoritative source files for the Hermes system context within NotebookLM. It categorizes files by their function, freshness, and suitability for system-level reasoning.

## Official NotebookLM Sources
These files represent the core system context and should be prioritized for daily synthesis.
- `/mnt/h/My Drive/Hermes_Workspace/Setup/2_states_master.txt`: System-state master (nightly).
- `/mnt/h/My Drive/Hermes_Workspace/Setup/3_runbooks_master.txt`: Runbook collection (nightly).
- `/mnt/h/My Drive/Hermes_Workspace/Setup/Hermes_OS_Core_Architecture.txt`: Core design principles (static).
- `/mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Event_Log_Rolling.txt`: Event stream and system activity (live).
- `/mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Live_Status.txt`: Current system health (live).

## Optional NotebookLM Sources
Use these to add historical depth or domain-specific context.
- `/mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Adjudication_History.txt`: Past system decisions.
- `/mnt/h/My Drive/Hermes_Workspace/Brain/reports/Personal_OS.md`: Personal OS design docs.
- `/mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Blockers_And_Human_Actions.txt`: Operational roadblocks.

## Files Not To Add
- Everything under `/mnt/h/My Drive/Hermes_Workspace/Setup/logs/`: Contains logs, state files, and curator history that clutter the reasoning window.
- `credentials.json`, `config.yaml`: Risk of data leakage.
- `*.sqlite`, `*.db`: NotebookLM cannot process raw binary databases.
- `*.lnk`, `desktop.ini`: OS noise.

## Source Freshness / Timestamp Evidence
- Master files (`2_states_master.txt`, `3_runbooks_master.txt`) contain header-block timestamps generated nightly by `nightly_brain_audit.sh`.
- Live logs (`Hermes_Event_Log_Rolling.txt`) contain ISO8601 timestamps per line entry.

## Refresh Mechanism
- Master files: Regenerated nightly (cron).
- Live logs: Continuous updates (appended).
- Architecture files: Manual update required.

## Manual NotebookLM Verification Prompt
"Using the attached source files, summarize the system state as of the latest nightly master file timestamp. Compare against the most recent 'Hermes_Live_Status.txt' for any drift."

## Recommended Next Step
Sync identified official sources to the active NotebookLM Hermes project space.

NotebookLM source register complete. Awaiting next instruction.