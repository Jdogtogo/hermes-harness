"""
Hermes Multi-Agent Harness v1 package.

Public surface:
    from harness.job_models  import HarnessJob, HarnessTask, ...
    from harness.roles       import ResearchAgent, MemoryStateAgent, ExecutionAgent
    from harness.supervisor  import Supervisor
    from harness.state_store import StateStore
    from harness.atomic_io   import atomic_json_write, atomic_json_read
    from harness.validators  import validate_job
"""
from harness.job_models import (
    HarnessJob,
    HarnessTask,
    AgentInput,
    AgentOutput,
    HarnessResult,
    HarnessError,
    JobStatus,
    RoleType,
)
from harness.roles import ResearchAgent, MemoryStateAgent, ExecutionAgent
from harness.supervisor import Supervisor
from harness.state_store import StateStore
from harness.atomic_io import atomic_json_write, atomic_json_read
from harness.validators import validate_job

__all__ = [
    "HarnessJob", "HarnessTask", "AgentInput", "AgentOutput",
    "HarnessResult", "HarnessError", "JobStatus", "RoleType",
    "ResearchAgent", "MemoryStateAgent", "ExecutionAgent",
    "Supervisor", "StateStore",
    "atomic_json_write", "atomic_json_read",
    "validate_job",
]
