"""
Supervisor layer for Hermes Multi-Agent Harness v1.

The Supervisor:
  1. Accepts a HarnessJob.
  2. Validates the job schema.
  3. Routes each task to the registered role.
  4. Validates each role's output.
  5. Accumulates errors and updates job status.
  6. Returns a validated HarnessResult.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import ValidationError

from roles import ExecutionAgent, MemoryStateAgent, ResearchAgent
from schema import (
    AgentInput,
    AgentOutput,
    HarnessError,
    HarnessJob,
    HarnessResult,
    JobStatus,
    RoleType,
)

# All registered roles.  Adding a new role type requires only an entry here.
_ROLE_REGISTRY: dict = {
    RoleType.research: ResearchAgent(),
    RoleType.memory_state: MemoryStateAgent(),
    RoleType.execution: ExecutionAgent(),
}


class Supervisor:
    """
    Routes HarnessJob tasks to the correct role and collects results.

    This is deterministic and synchronous.  Async orchestration is handled
    by the existing orchestrator_v2.py and is a separate concern.
    """

    def process(self, job: HarnessJob) -> HarnessResult:
        errors: list[HarnessError] = []
        task_outputs: list[AgentOutput] = []

        # --- Step 1: re-validate the job (defence-in-depth) ---
        try:
            HarnessJob.model_validate(job.model_dump())
        except ValidationError as exc:
            errors.append(
                HarnessError(
                    job_id=job.job_id,
                    error_type="job_validation_error",
                    message=str(exc),
                )
            )
            return HarnessResult(
                job_id=job.job_id,
                status=JobStatus.failed_validation,
                errors=errors,
            )

        # --- Step 2: process each task ---
        for task in job.tasks:
            agent_input = AgentInput(
                task_id=task.task_id,
                role_type=task.role_type,
                payload=task.payload,
            )

            role = _ROLE_REGISTRY.get(task.role_type)
            if role is None:
                errors.append(
                    HarnessError(
                        job_id=job.job_id,
                        task_id=task.task_id,
                        error_type="unknown_role",
                        message=f"No role registered for role_type: {task.role_type!r}",
                    )
                )
                return HarnessResult(
                    job_id=job.job_id,
                    status=JobStatus.failed_execution,
                    task_outputs=task_outputs,
                    errors=errors,
                )

            # Execute role
            try:
                output = role.run(agent_input)
            except Exception as exc:
                errors.append(
                    HarnessError(
                        job_id=job.job_id,
                        task_id=task.task_id,
                        error_type="execution_error",
                        message=str(exc),
                    )
                )
                return HarnessResult(
                    job_id=job.job_id,
                    status=JobStatus.failed_execution,
                    task_outputs=task_outputs,
                    errors=errors,
                )

            # Validate the output schema
            try:
                AgentOutput.model_validate(output.model_dump())
            except ValidationError as exc:
                errors.append(
                    HarnessError(
                        job_id=job.job_id,
                        task_id=task.task_id,
                        error_type="output_validation_error",
                        message=str(exc),
                    )
                )
                return HarnessResult(
                    job_id=job.job_id,
                    status=JobStatus.failed_validation,
                    task_outputs=task_outputs,
                    errors=errors,
                )

            # Check role-reported failure
            if not output.success:
                errors.append(
                    HarnessError(
                        job_id=job.job_id,
                        task_id=task.task_id,
                        error_type="role_reported_failure",
                        message=output.error_message or "role returned success=False",
                    )
                )
                return HarnessResult(
                    job_id=job.job_id,
                    status=JobStatus.failed_execution,
                    task_outputs=task_outputs,
                    errors=errors,
                )

            task_outputs.append(output)

        # --- Step 3: all tasks succeeded ---
        return HarnessResult(
            job_id=job.job_id,
            status=JobStatus.completed,
            task_outputs=task_outputs,
            errors=[],
            completed_at=datetime.now(timezone.utc).isoformat(),
        )
