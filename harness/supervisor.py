"""
Supervisor layer for Hermes Multi-Agent Harness v1.
"""
from __future__ import annotations

from datetime import datetime, timezone

from pydantic import ValidationError

from harness.job_models import (
    AgentInput, AgentOutput, HarnessError, HarnessJob, HarnessResult,
    JobStatus, RoleType, SafetyConfig,
)
from harness.roles import ExecutionAgent, MemoryStateAgent, ResearchAgent

_ROLE_REGISTRY: dict = {
    RoleType.research:     ResearchAgent(),
    RoleType.memory_state: MemoryStateAgent(),
    RoleType.execution:    ExecutionAgent(),
}


class Supervisor:
    def __init__(self, safety_config: SafetyConfig | None = None) -> None:
        self.safety_config = safety_config if safety_config is not None else SafetyConfig()

    def process(self, job: HarnessJob) -> HarnessResult:
        errors: list[HarnessError]  = []
        outputs: list[AgentOutput]  = []

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

        for task in job.tasks:
            inp = AgentInput(
                task_id=task.task_id,
                role_type=task.role_type,
                payload=task.payload,
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
