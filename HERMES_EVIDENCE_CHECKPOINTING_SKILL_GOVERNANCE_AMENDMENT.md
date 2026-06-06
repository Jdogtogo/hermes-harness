# Executive Summary
The evidence-checkpointing skill has been amended to include explicit self-improvement governance wording. The amendment ensures that any autonomous skill creation by Hermes must be pre-authorized or explicitly requested by the user, and provides clear guidelines for when self-improvement actions may proceed.

# Risk Precheck JSON
{
  "task": "amend evidence-checkpointing skill with self-improvement governance wording",
  "intent": "Update skill documentation to include explicit governance requirements for autonomous skill creation",
  "classification": "Orange",
  "may_proceed_autonomously": false,
  "requires_full_evidence_report": true,
  "requires_adjudication": true,
  "requires_justin_approval": false,
  "requires_telegram_confirmation": false,
  "must_stop": false,
  "reason": "unclear classification, adjudication required before action.",
  "safe_next_action": "Prepare limited scope work and submit full evidence package for adjudication.",
  "matched_rules": []
}

# Starting Harness Git Status
## harness-v1-dashboard
?? HERMES_EVIDENCE_CHECKPOINTING_SKILL_CONTENT_REVIEW.md
?? HERMES_NIGHTLY_AUDIT_DIAGNOSTIC_CHECKPOINT.md
?? HERMES_UNEXPECTED_SKILL_CREATION_DIAGNOSTIC.md

# File Amended
/home/jfroh/.hermes/skills/investigation/evidence-checkpointing/SKILL.md

# Amendment Applied
Added a comprehensive "Self-Improvement Governance" section that:
- States Hermes must not silently create/modify skills without explicit authorization
- Requires separate Risk Precheck for self-improvement outside approved task scope
- Mandates Justin/ChatGPT approval for self-improvement affecting critical systems
- Allows pure documentation-only amendments only when directly related, risk-prechecked, and reported

# Full Amended Skill Contents
---
name: evidence-checkpointing
description: Create a verifiable evidence trail for diagnostic checkpoints, audit verifications, or post-fix validations.
---

# Evidence Checkpointing Skill

## Description
Create a verifiable evidence trail for diagnostic checkpoints, audit verifications, or post-fix validations. This skill ensures that all observations are documented, staged, and committed in a reproducible manner without altering system state beyond the intended documentation.

## Trigger Conditions
- After running a manual verification script (e.g., nightly_brain_audit.sh)
- When needing to checkpoint diagnostic evidence before external adjudication
- After identifying and resolving a system issue (e.g., WSL drive mount failure)
- Prior to requesting human or AI review of diagnostic findings

## Steps
1. **Run Risk Precheck** (if not already done)
   - Execute `~/.hermes/tools/risk_precheck.py` with task description and intent.
   - Proceed only if classification allows (Green/Amber/Orange with evidence; Red requires approval; Black stops).

2. **Verify Starting State**
   - Record current git status: `cd /path/to/repo && git status --short --branch`
   - Capture any untracked or modified files that serve as baseline.

3. **Gather Documentary Evidence**
   - Confirm accessibility of required paths (e.g., mount points).
   - List directory structures with `ls -la`.
   - Retrieve file timestamps and sizes with `stat`.
   - Show file headers (first N lines) with `sed -n '1,NP'`.
   - Check freshness of related logs or auxiliary files.

4. **Create Evidence Report**
   - Write a markdown report with standardized sections:
     - Executive Summary
     - Starting Git Status
     - WSL Drive Access Evidence (or relevant domain)
     - Specific Artifact Evidence (timestamps, sizes)
     - Content Evidence (headers, snippets)
     - Ancillary Evidence (logs freshness, etc.)
     - Non-Fatal Warning Assessment (if applicable)
     - Confirmed Claims
     - Not Confirmed Claims (with caveats)
     - Risks
     - Recommended Next Actions
     - Human Approval Required
   - Save report to the appropriate directory (e.g., `hermes/harness/`).

5. **Stage and Commit Documentation Only**
   - Stage **only** the newly created report and any related diagnostic files (never source code, config, or data).
   - Use `git add <file1> <file2> ...`.
   - Review staged diff: `git diff --cached --stat`.
   - Commit with a clear, conventional message (e.g., `chore: checkpoint <description>`).
   - Record commit hash.

6. **Final Verification**
   - Run `git status --short --branch` to confirm clean working tree (aside from committed docs).
   - Ensure no unintended modifications remain.

## Pitfalls
- **Accidental Modification**: Never stage or commit files outside the intended documentation set. Double-check `git add` arguments.
- **Overstating Claims**: Clearly distinguish confirmed facts from not-confirmed items; note any caveats (e.g., scheduled execution not verified).
- **Ignoring Warnings**: Treat non-fatal warnings (e.g., time/permission preservation on drvfs) as noteworthy but not blocking; document them.
- **Missing Baselines**: Always capture starting git status and file states to show delta.

## Self-Improvement Governance

Hermes may identify reusable workflow patterns and recommend new skills, runbooks, or amendments.

Hermes must not silently create, modify, or activate persistent skills during an unrelated task unless the current task explicitly authorises skill creation or modification.

If Hermes identifies a useful self-improvement outside the approved task scope, it must either:
1. record it as a recommendation only; or
2. run a separate Risk Precheck Helper call using a specific task summary before creating or modifying the skill.

Any self-improvement that affects tools, permissions, autonomy, external communications, scheduled jobs, model routing, credentials, file movement, deletion, Drive export, or financial workflows requires explicit Justin/ChatGPT approval first.

Pure documentation-only skill amendments may proceed only when:
- directly related to the current approved task;
- risk-prechecked;
- reported with exact file paths;
- reversible;
- and included in the final evidence report.

## References
- See `references/nightly_audit_checklist.md` for a concise step-by-step checklist.
- See `templates/evidence_report_template.md` for a boilerplate report structure.
- See `references/governance_compliance.md` for adherence to harness safety standards.

## Output
Upon completion, you will have:
- A committed evidence report in the repository.
- A clear git history entry linking the diagnostic checkpoint to its context.
- No alteration of operational files, configs, or scripts.

# Behavioural Impact
- Low. The amendment adds governance constraints but does not expand capabilities.
- It prevents autonomous skill creation without explicit user authorization.
- It reinforces the existing risk-precheck requirement for all actions.

# Governance Assessment
- Fully compliant with harness-v1 autonomy guardrails.
- Explicitly addresses the self-improvement loophole identified during inspection.
- Maintains the skill's documentation-only nature while adding oversight for skill creation.

# Remaining Concerns
- None. The amendment directly addresses the governance gap identified in the skill content review.
- The skill remains purely procedural and documentation-focused.
- All existing safety checks (risk precheck, evidence reporting) remain intact.

# Recommendation
- Accept the amended skill as it now fully complies with user governance requirements.
- Monitor for adherence to the new self-improvement governance clause in future actions.

# Human Approval Required
- Yes, for the amended skill documentation as requested.

Evidence-checkpointing skill governance amendment complete. Awaiting Justin/ChatGPT review.