# Hermes Working Tree Evidence Report

## Executive Summary
The tree is **mixed/unsafe**. While the HEAD is at the manual-gated adjudication commit (`9e3a161`), the working tree contains significant modifications that diverge from this commit. These modifications are not merely transient; they represent a significant re-wiring of the harness tools and test suite, rendering the current working tree state inconsistent with the committed history.

## Current Branch and HEAD
- **Branch:** HEAD (Detached at 9e3a161)
- **HEAD Commit:** 9e3a161 ("feat: wire manual-gated ChatGPT 5.5 adjudicator call")

## Recent Commit History
- `9e3a161` (HEAD) feat: wire manual-gated ChatGPT 5.5 adjudicator call
- `eb39f2d` feat: add gated read-only research metadata adapter
- `05ae0c1` feat: add dry-run ChatGPT adjudication loop
- `c602627` chore: enforce guardrails in supervisor and state store
- `6b19210` docs: add guardrail enforcement report and update status doc
- `ee83f9f` chore: enforce guardrails before tool wiring
- `fa2a222` chore: fix stable harness import path
- `a5962cd` chore: add pre-tool-wiring guardrails
- `8a9e8ef` chore: add legacy_flat_layout/ to .gitignore, remove cached __pycache__ and state files from tracking
- `25ad1a9` chore: remove redundant legacy files and pycache

## Modified Files Evidence
- `harness/__init__.py`: Removed explicit imports of `atomic_io` and added `inspect_file_metadata`. Updated `__all__`.
- `harness/research_tools.py`: Major refactor: migrated from standalone function to `BaseModel`-based class approach.
- `harness/roles.py`: Refactored to handle `AuditEvent` and tool call dispatching via `payload` and `inspect_file_metadata`.
- `run_harness_smoke_test.py`: Updated logic to match the new `inspect_file_metadata` tool interface and agent invocation style.
- `tests/test_harness.py`: Updated test suite to align with the new `ResearchAgent` metadata tool invocation patterns.

## ResearchAgent Adapter Commit Status
- `eb39f2d` is in the history.
- The adapter code is committed, but the **working-tree modifications** represent a substantial, uncommitted evolution of that adapter (moving from standalone to class-based). It is currently in a state of "uncommitted working-tree change."

## Manual-Gated Adjudication Status
- `9e3a161` is HEAD.
- The adjudication code is committed. However, the modified files imply that the harness *must* be updated to maintain compatibility with the adjudication logic, or the modifications are testing infrastructure updates that weren't fully bundled with the adjudication commit.

## Untracked Artifact Assessment
- `HERMES_*.md`: Safe to archive (generated reports).
- `adjudication/live_extracted_response.json`: Safe to delete (ephemeral artifact).
- `symlink_test_escape.lnk`: Safe to delete (test artifact).

## Recommended Plan
1. **Archive reports:** `mkdir -p /home/jfroh/hermes/harness/archive/reports && mv /home/jfroh/hermes/harness/HERMES_*.md /home/jfroh/hermes/harness/archive/reports/`
2. **Remove artifacts:** `rm /home/jfroh/hermes/harness/adjudication/live_extracted_response.json /home/jfroh/hermes/harness/symlink_test_escape.lnk`
3. **Commit or Stash:** The tree modifications should be committed as a new "chore: update harness for metadata tool architecture" commit if they are confirmed stable, or `git stash` them if the current state is considered unstable/unverified.

Awaiting ChatGPT adjudication before further implementation.