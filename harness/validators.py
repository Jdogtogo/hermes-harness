"""
Validation helpers for Hermes Multi-Agent Harness v1.

Provides checks beyond what Pydantic enforces at construction time,
such as cross-field invariants and payload shape requirements.
"""
from __future__ import annotations

from typing import List, Tuple

from harness.job_models import HarnessJob, RoleType


def validate_job(job: HarnessJob) -> Tuple[bool, List[str]]:
    """
    Run full business-rule validation on a HarnessJob.

    Returns (ok, [error_messages]).
    If ok is True the list is empty.
    """
    errors: List[str] = []

    # Task IDs must be unique within the job
    seen: set = set()
    for task in job.tasks:
        if task.task_id in seen:
            errors.append(f"Duplicate task_id: {task.task_id!r}")
        seen.add(task.task_id)

    # Payload shape hints (warnings as errors for strict validation)
    for task in job.tasks:
        if task.role_type == RoleType.research:
            if "query" not in task.payload:
                errors.append(
                    f"Task {task.task_id!r}: research payload missing 'query' key"
                )
        elif task.role_type == RoleType.memory_state:
            for required in ("operation", "key"):
                if required not in task.payload:
                    errors.append(
                        f"Task {task.task_id!r}: memory_state payload missing {required!r} key"
                    )
        elif task.role_type == RoleType.execution:
            if "action" not in task.payload:
                errors.append(
                    f"Task {task.task_id!r}: execution payload missing 'action' key"
                )

    return (len(errors) == 0, errors)


def validate_agent_output_shape(output_dict: dict) -> Tuple[bool, str]:
    """
    Check that a raw dict has the required AgentOutput fields.

    Used when a role returns something that is not a typed AgentOutput.
    """
    required = {"task_id", "role_type", "result", "success"}
    missing  = required - output_dict.keys()
    if missing:
        return False, f"AgentOutput missing fields: {sorted(missing)}"
    return True, ""
