# HERMES_PHASE5A_DASHBOARD_EXPORT_REFRESH_DRY_RUN_V0_2

## Executive Summary
This document provides a dry-run analysis for the proposed autonomous refresh of the dashboard (`dashboard/report.html`) and Drive log exports, in accordance with the Phase 5A v0.2 policy. No files have been regenerated or exported.

## Policy Reference
[HERMES_PHASE5A_BOUNDED_SELF_MAINTENANCE_POLICY_V0_2.md](/home/jfroh/hermes/harness/HERMES_PHASE5A_BOUNDED_SELF_MAINTENANCE_POLICY_V0_2.md)

## Baseline Reference
Commit c81b5e9 -- chore: clean phase 5a documentation baseline

## Starting Git Status
## harness-v1-dashboard
?? HERMES_PHASE5A_BASELINE_CLEANUP_REPORT.md
?? HERMES_PHASE5A_DASHBOARD_REFRESH_DRY_RUN.md
?? HERMES_PHASE5A_TRANSIENT_ARTIFACT_CLEANUP_DRY_RUN.md

## Existing Dashboard/Export Files Found
- ./dashboard/report.html
- ./harness/dashboard_static.py
- ./harness/drive_log_exporter.py

## Existing References Found
- harness/dashboard_static.py:179:    output_file = output_dir / "report.html"
- harness/drive_log_exporter.py:14:    def export(self):
- harness/drive_log_exporter.py:34:        self.export_live_status(events)
- harness/drive_log_exporter.py:35:        self.export_rolling_log(events)
- harness/drive_log_exporter.py:36:        self.export_adjudication_history(events)
- harness/drive_log_exporter.py:37:        self.export_blockers_and_actions(events)
- harness/drive_log_exporter.py:38:        self.export_infrastructure_state(events)
- harness/drive_log_exporter.py:39:        self.export_daily_summary(events)
- harness/drive_log_exporter.py:43:    def export_live_status(self, events):
- harness/drive_log_exporter.py:49:    def export_rolling_log(self, events)
- harness/drive_log_exporter.py:54:    def export_adjudication_history(self, events)
- harness/drive_log_exporter.py:60:    def export_blockers_and_actions(self, events)
- harness/drive_log_exporter.py:66:    self.export_infrastructure_state(events)
- harness/drive_log_exporter.py:71:    self.export_daily_summary(events)
- harness/drive_log_exporter.py:79:    exporter = DriveLogExporter(event_file, DRIVE_TARGET)
- harness/drive_log_exporter.py:80:    if exporter.export():
- harness/drive_log_exporter.py:81:        print("Drive export successful")
- harness/drive_log_exporter.py:83:        print("Drive export failed or skipped")
- tests/test_dashboard_static.py:10:from harness.dashboard_static import DashboardGenerator
- tests/test_dashboard_static.py:137:    from harness.dashboard_static import main
- tests/test_drive_log_exporter.py:10:from harness.drive_log_exporter import DriveLogExporter
- tests/test_drive_log_exporter.py:12:def test_drive_exporter_success():\n... (truncated)

## Candidate Refresh Targets
- dashboard/report.html (local file)
- Drive log exports (remote files on Google Drive)

## Classification Table
| Target | Classification | Reason | Risk |
| :--- | :--- | :--- | :--- |
| dashboard/report.html | Approved for future refresh | Output of dashboard generator, safe to regenerate | Low |
| Drive log exports (live status, rolling log, adjudication history, blockers/actions, infrastructure state, daily summary) | Approved for future refresh | Safe Drive refresh via exporter, append-only or overwrite with same schema | Low |

## Proposed Refresh Plan
- `python3 harness/dashboard_static.py` (regenerates dashboard/report.html)
- `python3 harness/drive_log_exporter.py` (refreshes Drive log exports)

## Files To Keep Read-Only
- harness/dashboard_static.py (script)
- harness/drive_log_exporter.py (script)
- tests/ (test files)

## Files Requiring Human Review
- None identified.

## Exclusions
- No other dashboard or Drive exporter targets identified.

## Risks
- Low: The dashboard regeneration overwrites a local file; the Drive export overwrites existing Drive files with same schema. Both are idempotent and reversible via git (for dashboard) or Drive version history (for Drive files).

## Rollback Notes
- Dashboard: Revert via `git checkout dashboard/report.html` or previous commit.
- Drive exports: Revert via Google Drive version history if needed.

## Recommendation
- Proceed with approval for the proposed refresh list.

## Human Approval Required Before Action
- Explicit sign-off required for the above refresh tasks.

Phase 5A dashboard/export refresh dry-run v0.2 complete. Awaiting Justin/ChatGPT review.