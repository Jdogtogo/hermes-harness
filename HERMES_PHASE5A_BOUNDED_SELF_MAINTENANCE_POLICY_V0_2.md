# HERMES_PHASE5A_BOUNDED_SELF_MAINTENANCE_POLICY_V0_2

## Executive Summary
Phase 5A (v0.2) establishes the first "Safe Autonomy" tier for Hermes, narrowly scoped to local self-maintenance within the Harness v1. This policy defines the authorized set of low-risk housekeeping tasks to enable controlled, auditable, and self-contained maintenance.

## Purpose of Phase 5A
To transition Hermes from "Observe-Report" to "Safe-Self-Maintainer" for an approved list of low-risk local system artifacts, reducing manual overhead while maintaining absolute safety guardrails.

## Current Approved Capabilities
- Dashboard reporting (read-only).
- Local Drive log exports.
- Audit loop validation.
- Smoke testing within bounded verification loops.

## New Capabilities Proposed
- Autonomous handling of a narrow approved set of low-risk local housekeeping tasks inside /home/jfroh/hermes/harness/, limited initially to observation, reporting, approved report archival, known temporary artifact cleanup, dashboard regeneration, Drive log export refresh, and source timestamp checks.

## Allowed Autonomous Actions
- regenerate dashboard/report.html
- refresh safe Drive log exports
- archive approved report files from harness root into archive/reports_YYYYMMDD/
- remove known transient test artifacts only, such as symlink_test_escape.lnk and .tmp files older than 24 hours inside approved temp/output folders
- check timestamps on NotebookLM master files
- run read-only health checks
- produce evidence reports
- Detection and reporting of file permission inconsistencies. (Permission changes require human approval unless a specific permission-fix task has been separately dry-run, adjudicated, and approved.)

## Prohibited Actions
- Any network-outbound action (except local-to-Drive logging).
- Modification of production configurations.
- Modification of model routing, API keys, or security credentials.
- Execution of financial transactions or personal bookings.
- Any action bypassing the Adjudication Packet process for L3+ tasks.
- No chmod/chown/permission changes without explicit approval.
- No deletion outside approved transient artifacts.
- No changes outside /home/jfroh/hermes/harness/ without explicit approval.
- No edits to ~/.hermes scripts during Phase 5A autonomous mode.
- No cron edits.
- No Drive folder restructuring.
- No source-file overwrites except the already-approved dashboard/exporter generated outputs.

## Required Evidence for Each Action
- Adjudication Packet (Goal, Plan, Rationale).
- Pre-action git status.
- Exact target paths.
- Allowed-action category.
- Command run.
- Event stream entry.
- Post-action verification.
- Final git status.
- Rollback note if applicable.

## Stop Conditions
- Detection of any unauthorized filesystem access.
- Failure of any smoke test within the harness.
- Execution-time metrics exceeding established baseline.
- Manual `--interrupt` command.
- Dirty git state before action unless task is explicitly report archival.
- Target path outside approved allowlist.
- Command would alter config, scripts, credentials, cron, model routing, booking systems, or financial/client data.
- Drive path unavailable where Drive export is required.

## Escalation Conditions
- Persistent failure of an autonomous maintenance task (3 retries).
- Detection of state mismatch not automatically resolved.
- Critical hardware/environment metric violation (e.g., disk capacity < 5%).

## Quiet-Hours Behaviour
- Proactive maintenance must pause entirely between 21:30 and 07:00.
- Exception: If the system is in an unstable state at 21:30, it must log the state and enter sleep mode until 07:00.

## Git Cleanliness Rules
- All maintenance tasks must start with a clean working tree.
- Changes must be isolated on local maintenance branches (e.g., `maint/yyyy-mm-dd`).
- Final verification requires a clean working tree status.

## Event Stream Requirements
- Every action must push a structured JSON event to the local event stream: `{timestamp, action, target, result, phase}`.

## Dashboard/Drive Export Requirements
- Verification of export integrity via checksum before the task is marked "COMPLETE".

## Examples of Approved Level 3 Tasks
- `rotate_audit_logs`: Moving logs to dated archive folder.
- `cleanup_temp_dir`: Removing `.tmp` files older than 24h.
- `refresh_dashboard`: Regenerating dashboard/report.html.

## Examples Requiring Human Approval
- Archiving of non-maintenance data.
- Modification of any file outside the approved Harness tree.
- Any action causing a state change in the personal/financial automation stack.

## Acceptance Criteria for Enabling Phase 5A
- Completion of ChatGPT adjudication for this policy.
- One dry-run report for approved report archival.
- One dry-run report for transient artifact cleanup.
- One dry-run report for dashboard/export refresh.
- ChatGPT adjudication accepts the dry-run results.
- A single Level 3 task is then enabled first, not the entire Phase 5A set.

## Recommended Implementation Plan
1. Review and Adjudication by Justin/ChatGPT.
2. Dry-run maintenance scripts in Observation Mode (Level 2).
3. Enable Level 3 (Autonomous) for a single, low-risk task.
4. Monitor event stream for 24 hours.

Phase 5A policy v0.2 complete. Awaiting Justin/ChatGPT review.