"""
Supervisor layer for Hermes Multi-Agent Harness v1.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import ValidationError

from harness.job_models import (
    AgentInput, AgentOutput, AuditEvent, AuditStatus, HarnessError, HarnessJob, HarnessResult,
    JobStatus, RoleType, SafetyConfig, ToolCategory,
)
from harness.roles import ExecutionAgent, MemoryStateAgent, ResearchAgent
from harness.state_store import StateStore
from harness.validators import validate_tool_access

_ROLE_REGISTRY: dict = {
    RoleType.research:     ResearchAgent(),
    RoleType.memory_state: MemoryStateAgent(),
    RoleType.execution:    ExecutionAgent(),
}

_ROLE_CATEGORY_MAP: dict[RoleType, set[ToolCategory]] = {
    RoleType.research:     {ToolCategory.research},
    RoleType.memory_state: {ToolCategory.memory},
    RoleType.execution:    {ToolCategory.execution},
}


class Supervisor:
    def __init__(
        self,
        safety_config: SafetyConfig | None = None,
        state_store: StateStore | None = None,
    ) -> None:
        self.safety_config = safety_config if safety_config is not None else SafetyConfig()
        self.state_store = state_store

    def _new_event_id(self, job_id: str, task_id: str) -> str:
        return f"evt-{job_id}-{task_id}-{uuid.uuid4().hex[:8]}"

    def _write_audit(
        self,
        job_id: str,
        task_id: str,
        role_type: RoleType,
        category: ToolCategory | None,
        action: str,
        status: AuditStatus,
        message: str,
    ) -> None:
        if self.state_store is None:
            return
        self.state_store.write_audit_event(
            job_id,
            AuditEvent(
                event_id=self._new_event_id(job_id, task_id),
                job_id=job_id,
                task_id=task_id,
                role_type=role_type,
                proposed_tool_category=category,
                action=action,
                status=status,
                message=message,
            ),
        )

    def process(self, job: HarnessJob) -> HarnessResult:
        errors: list[HarnessError] = []
        outputs: list[AgentOutput] = []

        if len(job.tasks) > self.safety_config.max_steps:
            errors.append(HarnessError(
                job_id=job.job_id,
                error_type="max_steps_exceeded",
                message=(
                    f"Job has {len(job.tasks)} tasks, which exceeds "
                    f"SafetyConfig.max_steps={self.safety_config.max_steps}"
                ),
            ))
            return HarnessResult(
                job_id=job.job_id,
                status=JobStatus.failed_validation,
                errors=errors,
            )

        try:
            HarnessJob.model_validate(job.model_dump())
        except ValidationError as exc:
            errors.append(HarnessError(
                job_id=job.job_id,
                error_type="job_validation_error",
                message=str(exc),
            ))
            return HarnessResult(
                job_id=job.job_id,
                status=JobStatus.failed_validation,
                errors=errors,
            )

        for task in job.tasks:
            if "safety_config" in task.payload:
                errors.append(HarnessError(
                    job_id=job.job_id,
                    task_id=task.task_id,
                    error_type="safety_config_override_attempt",
                    message=(
                        "Task payload contains 'safety_config', which is "
                        "not allowed.  The supervisor's SafetyConfig is "
                        "authoritative."
                    ),
                ))
                return HarnessResult(
                    job_id=job.job_id,
                    status=JobStatus.failed_validation,
                    errors=errors,
                )

        if "safety_config" in job.metadata:
            errors.append(HarnessError(
                job_id=job.job_id,
                error_type="safety_config_override_attempt",
                message=(
                    "Job metadata contains 'safety_config', which is "
                    "not allowed.  The supervisor's SafetyConfig is "
                    "authoritative."
                ),
            ))
            return HarnessResult(
                job_id=job.job_id,
                status=JobStatus.failed_validation,
                errors=errors,
            )

        has_audit = self.state_store is not None

        for task in job.tasks:
            is_real_tool_request = "tool" in task.payload

            if is_real_tool_request:
                # Real tool path: validate, audit, gate.
                category = list(
                    _ROLE_CATEGORY_MAP.get(task.role_type, {ToolCategory.execution})
                )[0]

                self._write_audit(
                    job.job_id, task.task_id, task.role_type, category,
                    action="tool_access_attempted",
                    status=AuditStatus.pending,
                    message=f"Tool request: {task.payload.get('tool')!r}",
                )

                allowed, msg = validate_tool_access(
                    self.safety_config,
                    task.role_type,
                    category,
                    has_audit_context=has_audit,
                )
                if not allowed:
                    self._write_audit(
                        job.job_id, task.task_id, task.role_type, category,
                        action="tool_access_denied",
                        status=AuditStatus.blocked,
                        message=msg,
                    )
                    errors.append(HarnessError(
                        job_id=job.job_id,
                        task_id=task.task_id,
                        error_type="tool_access_blocked",
                        message=msg,
                    ))
                    return HarnessResult(
                        job_id=job.job_id,
                        status=JobStatus.failed_execution,
                        task_outputs=outputs,
                        errors=errors,
                    )

                self._write_audit(
                    job.job_id, task.task_id, task.role_type, category,
                    action="tool_access_allowed",
                    status=AuditStatus.allowed,
                    message="Access granted",
                )
            else:
                category = None  # stub execution; no tool category relevant

            inp = AgentInput(
                task_id=task.task_id,
                role_type=task.role_type,
                payload=task.payload,
                safety_config=self.safety_config,
                has_audit_context=has_audit,
            )
            role = _ROLE_REGISTRY.get(task.role_type)
            if role is None:
                errors.append(HarnessError(
                    job_id=job.job_id,
                    task_id=task.task_id,
                    error_type="unknown_role",
                    message=f"No role registered for role_type={task.role_type!r}",
                ))
                return HarnessResult(
                    job_id=job.job_id,
                    status=JobStatus.failed_execution,
                    task_outputs=outputs,
                    errors=errors,
                )
            try:
                output = role.run(inp)
            except Exception as exc:
                errors.append(HarnessError(
                    job_id=job.job_id,
                    task_id=task.task_id,
                    error_type="execution_error",
                    message=str(exc),
                ))
                return HarnessResult(
                    job_id=job.job_id,
                    status=JobStatus.failed_execution,
                    task_outputs=outputs,
                    errors=errors,
                )

            try:
                AgentOutput.model_validate(output.model_dump())
            except ValidationError as exc:
                errors.append(HarnessError(
                    job_id=job.job_id,
                    task_id=task.task_id,
                    error_type="output_validation_error",
                    message=str(exc),
                ))
                return HarnessResult(
                    job_id=job.job_id,
                    status=JobStatus.failed_validation,
                    task_outputs=outputs,
                    errors=errors,
                )

            if is_real_tool_request:
                if output.success:
                    self._write_audit(
                        job.job_id, task.task_id, task.role_type, category,
                        action="tool_execution_succeeded",
                        status=AuditStatus.allowed,
                        message="Tool completed successfully",
                    )
                else:
                    self._write_audit(
                        job.job_id, task.task_id, task.role_type, category,
                        action="tool_execution_failed",
                        status=AuditStatus.rejected,
                        message=output.error_message or "role returned success=False",
                    )

            if not output.success:
                errors.append(HarnessError(
                    job_id=job.job_id,
                    task_id=task.task_id,
                    error_type="role_reported_failure",
                    message=output.error_message or "role returned success=False",
                ))
                return HarnessResult(
                    job_id=job.job_id,
                    status=JobStatus.failed_execution,
                    task_outputs=outputs,
                    errors=errors,
                )
            outputs.append(output)

        return HarnessResult(
            job_id=job.job_id,
            status=JobStatus.completed,
            task_outputs=outputs,
            errors=[],
            completed_at=datetime.now(timezone.utc).isoformat(),
        )
