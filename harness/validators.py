"""
Validation helpers for Hermes Multi-Agent Harness v1.
"""
from __future__ import annotations

from typing import List, Tuple

from harness.job_models import HarnessJob, RoleType, SafetyConfig, ToolCategory


_ROLE_CATEGORY_MAP: dict[RoleType, set[ToolCategory]] = {
    RoleType.research:     {ToolCategory.research},
    RoleType.memory_state: {ToolCategory.memory},
    RoleType.execution:    {ToolCategory.execution},
}


def validate_job(job: HarnessJob) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    seen: set = set()
    for task in job.tasks:
        if task.task_id in seen:
            errors.append(f"Duplicate task_id: {task.task_id!r}")
        seen.add(task.task_id)
    for task in job.tasks:
        if task.role_type == RoleType.research:
            if "query" not in task.payload:
                errors.append(
                    f"Task {task.task_id!r} (research) payload is missing 'query'"
                )
        elif task.role_type == RoleType.memory_state:
            if "operation" not in task.payload:
                errors.append(
                    f"Task {task.task_id!r} (memory_state) payload is missing 'operation'"
                )
        elif task.role_type == RoleType.execution:
            if "action" not in task.payload:
                errors.append(
                    f"Task {task.task_id!r} (execution) payload is missing 'action'"
                )
    return (len(errors) == 0, errors)


def validate_tool_access(
    config: SafetyConfig,
    role_type: RoleType,
    category: ToolCategory,
    has_audit_context: bool = False
) -> tuple[bool, str]:
    if config.deterministic_only:
        return False, "Guardrail violation: Deterministic mode is active (deterministic_only=True)"
    if not config.allow_real_tool_calls:
        return False, "Guardrail violation: Real tool calls are disabled (allow_real_tool_calls=False)"
    allowed_categories = _ROLE_CATEGORY_MAP.get(role_type, set())
    if category not in allowed_categories:
        return (
            False,
            f"Guardrail violation: Role {role_type!r} is not allowed to request "
            f"tool category {category!r}",
        )
    if category not in config.allowed_tool_categories:
        return False, f"Guardrail violation: Tool category {category!r} is not in allowlist"
    if config.require_audit_log and not has_audit_context:
        return False, "Guardrail violation: Audit logging required, but no audit context provided"
    return True, "Access granted"
