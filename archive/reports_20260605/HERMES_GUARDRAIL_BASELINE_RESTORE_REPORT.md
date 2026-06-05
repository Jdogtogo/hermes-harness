# Hermes Guardrail Baseline Restore Report

## Executive Summary
Clean guardrail baseline restored. All premature ResearchAgent tool work removed, leaving only the enforced guardrail foundation.

## Git State Before Restore
- Status: Two untracked markdown reports (HERMES_GUARDRAIL_ADJUDICATION_CLARIFICATION.md, HERMES_RESEARCH_TOOL_ADAPTER_REPORT.md) and one commit (c517bb2) adding read-only research file metadata tool.
- Recent commits:
  c517bb2 feat: add read-only research file metadata tool
  c602627 chore: enforce guardrails in supervisor and state store
  6b19210 docs: add guardrail enforcement report and update status doc
  ee83f9f chore: enforce guardrails before tool wiring
  fa2a222 chore: fix stable harness import path
  a5962cd chore: add pre-tool-wiring guardrails
  8a9e8ef chore: add legacy_flat_layout/ to .gitignore, remove cached __pycache__ and state files from tracking
  25ad1a9 chore: remove redundant legacy files and pycache

## Premature Research Tool Changes Found
- Commit c517bb2: added research_tools.py, updated __init__.py and roles.py to import and use inspect_file_metadata.
- Files: harness/research_tools.py, harness/__init__.py (import line), harness/roles.py (import line and usage in ResearchAgent).
- No other research-tool-specific tests were present; the test suite remained at 44 tests (guardrail only).

## Rollback Actions Taken
1. Removed the file harness/research_tools.py.
2. Removed the import line from harness/__init__.py.
3. Removed the import line and all usage of inspect_file_metadata from harness/roles.py, restoring ResearchAgent to a pure stub role.
4. Developed the two premature markdown reports (HERMES_GUARDRAIL_ADJUDICATION_CLARIFICATION.md and HERMES_RESEARCH_TOOL_ADAPTER_REPORT.md) were deleted as they are no longer relevant.
5. Reset the repository to the state at commit c602627 (the last guardrail enforcement commit before the research tool addition), ensuring all guardrail changes are preserved.

## Exact Import Path Verification
- repr(harness.__file__): '/home/jfroh/hermes/harness/harness/__init__.py'
- underscore-safe output: /home/jfroh/hermes/harness/harness/[UNDERSCORE][UNDERSCORE]init[UNDERSCORE][UNDERSCORE].py
  (contains [UNDERSCORE][UNDERSCORE]init[UNDERSCORE][UNDERSCORE].py as required)

## Guardrail Baseline Verification
- SafetyConfig exports: OK
- validate_tool_access exports: OK
- no /tmp/harness references: grep returned no matches (exit code 1)
- drift diagnostic passes: test_existing_drift_diagnostic_still_runs PASSED
- smoke test passes: run_harness_smoke_test.py exited 0
- pytest passes: 44/44 tests passed
- zero DeprecationWarning: no warnings in test output

## Default SafetyConfig Behaviour
- deterministic_only: True
- allow_real_tool_calls: False
- default config blocks real tool categories: verified by test_default_safety_config_blocks_all_real_tool_calls PASSED and the exhaustive validation test output (all combinations blocked).
- deterministic stubs can run without real tool access: verified by stub role tests (test_research_agent_returns_stub, etc.) and the test_deterministic_only_allows_stub_roles PASSED.

## Git Status After Restore
- On branch: (no branch, detached HEAD at c602627)
- Untracked files: HERMES_GUARDRAIL_BASELINE_RESTORE_REPORT.md (this file)
- No modified or deleted files; the working tree is clean aside from this report.

## Current Maturity Classification
Safe Harness v1 foundation with enforced pre-tool-wiring guardrails.

## Recommended Next Step
Prepare to re-run the first read-only ResearchAgent metadata adapter phase, but only after ChatGPT approval.

Awaiting ChatGPT adjudication before further implementation.