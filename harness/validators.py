"""
Validation logic for Hermes Multi-Agent Harness v1.
"""
from __future__ import annotations

from typing import List, Tuple

from harness.job_models import SafetyConfig, ToolCategory, RoleType, HarnessJob

def validate_job(job: HarnessJob) -> Tuple[bool, List[str]]:
    """Validate a HarnessJob for basic correctness."""
    errors: List[str] = []
    if not job.job_id or not job.job_id.strip():
        errors.append("job_id must not be blank")
    if not job.tasks:
        errors.append("tasks must contain at least one task")
    else:
        task_ids = [t.task_id for t in job.tasks]
        if len(task_ids) != len(set(task_ids)):
            errors.append("duplicate task IDs are not allowed")
    return (len(errors) == 0, errors)


def validate_tool_access(
    config: SafetyConfig,
    role_type: RoleType,
    category: ToolCategory,
    has_audit_context: bool = False
) -> tuple[bool, str]:
    """
    Validates if a tool call is permitted based on current SafetyConfig.
    """
    if config.deterministic_only:
        return False, "Guardrail violation: Deterministic mode is active (deterministic_only=True)"

    if not config.allow_real_tool_calls:
        return False, "Guardrail violation: Real tool calls are disabled (allow_real_tool_calls=False)"

    if category not in config.allowed_tool_categories:
        return False, f"Guardrail violation: Tool category {category!r} is not in allowlist"

    if config.require_audit_log and not has_audit_context:
        return False, "Guardrail violation: Audit logging required, but no audit context provided"

    return True, "Access granted"
