"""
Pydantic models for Hermes Multi-Agent Harness v1.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class JobStatus(str, Enum):
    queued             = "queued"
    validating         = "validating"
    running            = "running"
    failed_validation  = "failed_validation"
    failed_execution   = "failed_execution"
    completed          = "completed"


class RoleType(str, Enum):
    research     = "research"
    memory_state = "memory_state"
    execution    = "execution"


class AuditStatus(str, Enum):
    pending  = "pending"
    allowed  = "allowed"
    blocked  = "blocked"
    rejected = "rejected"


class HarnessTask(BaseModel):
    task_id:   str
    role_type: RoleType
    payload:   Dict[str, Any] = Field(default_factory=dict)

    @field_validator("task_id")
    @classmethod
    def task_id_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("task_id must not be blank")
        return v


class HarnessJob(BaseModel):
    job_id:   str
    tasks:    List[HarnessTask]
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("job_id")
    @classmethod
    def job_id_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("job_id must not be blank")
        return v

    @field_validator("tasks")
    @classmethod
    def tasks_not_empty(cls, v: List[HarnessTask]) -> List[HarnessTask]:
        if len(v) < 1:
            raise ValueError("tasks must contain at least one task")
        return v


class AgentInput(BaseModel):
    task_id:   str
    role_type: RoleType
    payload:   Dict[str, Any]


class AgentOutput(BaseModel):
    task_id:       str
    role_type:     RoleType
    result:        Dict[str, Any]
    success:       bool = True
    error_message: Optional[str] = None


class HarnessError(BaseModel):
    job_id:     str
    task_id:    Optional[str] = None
    error_type: str
    message:    str
    timestamp:  str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class HarnessResult(BaseModel):
    job_id:       str
    status:       JobStatus
    task_outputs: List[AgentOutput]         = Field(default_factory=list)
    errors:       List[HarnessError]        = Field(default_factory=list)
    completed_at: Optional[str]             = None


class ToolCategory(str, Enum):
    research  = "research"
    memory    = "memory"
    execution = "execution"


class SafetyConfig(BaseModel):
    deterministic_only: bool = True
    allow_real_tool_calls: bool = False
    allowed_tool_categories: list[ToolCategory] = []
    require_audit_log: bool = True
    max_steps: int = 5
    timeout_seconds: int = 60


class AuditEvent(BaseModel):
    event_id: str
    job_id: str
    task_id: str
    role_type: RoleType
    proposed_tool_category: ToolCategory | None
    action: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    status: AuditStatus
    message: str

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_be_utc_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware (use timezone.utc)")
        return v
