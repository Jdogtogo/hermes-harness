# HERMES_PHASE5A_BOUNDED_SELF_MAINTENANCE_POLICY

## Executive Summary
Phase 5A establishes the first "Safe Autonomy" tier for Hermes, specifically focused on local self-maintenance within the existing Harness v1. It builds upon the established Mission/Trust Framework and Operating Rules v1 to enable controlled, auditable, and self-contained maintenance tasks without human intervention for every minor action.

## Purpose of Phase 5A
To transition Hermes from "Observe-Report" to "Safe-Self-Maintainer" for non-critical, low-stakes local system artifacts, reducing cognitive load on Justin by resolving routine loose ends autonomously while maintaining strict safety guardrails.

## Current Approved Capabilities
- Dashboard reporting (read-only).
- Local Drive log exports.
- Audit loop validation.
- Smoke testing within bounded verification loops.

## New Capabilities Proposed
- Autonomous triage and local repair of prioritized Priority 1 "Loose Ends" (e.g., stale temporary files, broken local symlinks, missing log headers, audit file cleanup) within the `/home/jfroh/hermes/harness/` tree.

## Allowed Autonomous Actions
- Cleanup of temporary build artifacts/log segments.
- Rotation and archival of local audit reports.
- Correction of file permission inconsistencies (within `/home/jfroh/hermes/`).
- Refresh of non-sensitive local status dashboards.

## Prohibited Actions
- Any network-outbound action (except local-to-Drive logging).
- Modification of production configurations.
- Modification of model routing, API keys, or security credentials.
- Execution of financial transactions or personal bookings.
- Any action bypassing the Adjudication Packet process for L3+ tasks.

## Required Evidence for Each Action
- Adjudication Packet (Goal, Plan, Rationale).
- Pre-action hash/state validation.
- JSON-structured log of changes made.
- Post-action verification (status code/git checkpoint).

## Stop Conditions
- Detection of any unauthorized filesystem access.
- Failure of any smoke test within the harness.
- Execution-time metrics exceeding established baseline.
- Manual `--interrupt` command.

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
- `verify_manifest`: Running hash check on critical config files.

## Examples Requiring Human Approval
- Archiving of non-maintenance data.
- Modification of any file outside the approved Harness tree.
- Any action causing a state change in the personal/financial automation stack.

## Acceptance Criteria for Enabling Phase 5A
- Completion of ChatGPT adjudication for this policy.
- Successful dry-run of the "rotate_audit_logs" task in Level 2 (Observe/Report).
- Validation of JSON logging output.

## Recommended Implementation Plan
1. Review and Adjudication by Justin/ChatGPT.
2. Dry-run maintenance scripts in Observation Mode (Level 2).
3. Enable Level 3 (Autonomous) for a single, low-risk task (e.g., log rotation).
4. Monitor event stream for 24 hours.

Phase 5A bounded self-maintenance policy draft complete. Awaiting Justin/ChatGPT review.