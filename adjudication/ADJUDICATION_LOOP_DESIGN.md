# Adjudication Loop Design

## Overview
This document describes the intended adjudication loop for the Hermes Multi-Agent Harness.
The loop is designed to provide a conservative, evidence-based gatekeeper phase between implementation steps.
As of now, the approval mode is set to `manual` and the loop is not active.

## Components
1. **Hermes Implementation Agent**: Produces work and requests adjudication for a completed phase.
2. **Adjudication Request**: A JSON document (see example) that includes the phase summary, evidence, and claimed maturity.
3. **Adjudicator (ChatGPT 5.5)**: Evaluates the request against the system prompt and schema, returning a decision.
4. **Adjudication Response**: A JSON document (validated by the schema) that dictates the next action.

## Flow (When Enabled)
1. Implementation Agent completes a phase and writes an adjudication request to a designated location.
2. The adjudicator (via the `auxiliary.approval` provider) is invoked with the request and system prompt.
3. The adjudicator returns a JSON response adhering to the schema.
4. A validation script checks the response for structural and logical correctness.
5. Based on the `decision` field:
   - `approved`: The Implementation Agent may proceed to the phase named in `next_instruction_for_hermes`.
   - `revise`: The Implementation Agent must address the `blocking_issues` and resubmit a new request.
   - `rejected`: The phase is considered failed; a new approach is needed.
   - `stop`: Human intervention is required; the loop halts until manual reset.
6. The `should_continue` flag is used to prevent automatic advancement when not approved.

## Current State
- The adjudicator is configured but the approval mode is `manual`.
- No automatic invocation of the adjudicator is wired into the harness.
- The design is ready for a future phase where `approvals.mode` is changed to `automatic` (or similar) and the loop is activated.

## Safety Notes
- The adjudicator is instructed to be conservative and evidence-based.
- The schema requires that `should_continue` is only `true` when `decision` is `approved`.
- The loop does not have autonomous tool wiring or LLM role execution; it only governs phase transitions.