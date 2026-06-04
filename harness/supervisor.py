"""
Supervisor layer for Hermes Multi-Agent Harness v1.

Accepts a HarnessJob, validates it, routes each task to the registered
role, validates the output, and returns a HarnessResult.
"""
from __future__ import annotations

from datetime import datetime, timezone

from pydantic import ValidationError

from harness.job_models import (
    AgentInput,
    AgentOutput,
    HarnessError,
    HarnessJob,
    HarnessResult,
    JobStatus,
    RoleType,
)
from harness.roles import ExecutionAgent, MemoryStateAgent, ResearchAgent

_ROLE_REGISTRY: dict = {
    RoleType.research:     ResearchAgent(),
    RoleType.memory_state: MemoryStateAgent(),
    RoleType.execution:    ExecutionAgent(),
}


class Supervisor:
    """
    Routes HarnessJob tasks to roles and collects HarnessResult.

    Deterministic and synchronous.  All paths return a HarnessResult;
    exceptions are caught and converted to errors — the supervisor
    never propagates exceptions to the caller.
    """

    def process(self, job: HarnessJob) -> HarnessResult:
        errors: list[HarnessError]  = []
        outputs: list[AgentOutput]  = []

        # ── Step 1: re-validate job (defence-in-depth) ─────────────────────
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

        # ── Step 2: process each task ───────────────────────────────────────
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

            # Execute
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

            # Validate output schema
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

            # Check role-reported failure
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

        # ── Step 3: completed ───────────────────────────────────────────────
        return HarnessResult(
            job_id=job.job_id,
            status=JobStatus.completed,
            task_outputs=outputs,
            errors=[],
            completed_at=datetime.now(timezone.utc).isoformat(),
        )
