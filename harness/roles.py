"""
Minimal role abstractions for Hermes Multi-Agent Harness v1.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from harness.job_models import (
    AgentInput, AgentOutput, AuditEvent, AuditStatus, RoleType, SafetyConfig, ToolCategory,
)
from harness.research_tools import inspect_file_metadata
from harness.state_store import StateStore


class BaseRole:
    name:      str      = "BaseRole"
    role_type: RoleType

    def _check_role_type(self, inp: AgentInput) -> tuple[bool, str]:
        if inp.role_type != self.role_type:
            return (
                False,
                f"role type mismatch: {self.name} expects {self.role_type!r}, "
                f"received {inp.role_type!r}",
            )
        return True, ""

    def _failure(self, inp: AgentInput, message: str) -> AgentOutput:
        return AgentOutput(
            task_id=inp.task_id,
            role_type=inp.role_type,
            result={},
            success=False,
            error_message=message,
        )

    def run(self, inp: AgentInput) -> AgentOutput:
        raise NotImplementedError(f"{self.name}.run() is not implemented")


class ResearchAgent(BaseRole):
    name      = "ResearchAgent"
    role_type = RoleType.research

    def run(self, inp: AgentInput) -> AgentOutput:
        ok, err = self._check_role_type(inp)
        if not ok:
            return self._failure(inp, err)
        payload = inp.payload or {}
        tool = payload.get("tool")
        if tool == "file_metadata":
            return self._run_file_metadata_tool(inp, payload)
        query = payload.get("query", "")
        return AgentOutput(
            task_id=inp.task_id,
            role_type=self.role_type,
            result={
                "query":    query,
                "findings": f"[STUB] No real research performed for: {query!r}",
            },
            success=True,
        )

    def _run_file_metadata_tool(self, inp: AgentInput, payload: dict) -> AgentOutput:
        path = payload.get("path", "")
        safety_config_dict = payload.get("safety_config", {})
        if isinstance(safety_config_dict, dict):
            safety_config = SafetyConfig(**safety_config_dict)
        else:
            safety_config = safety_config_dict or SafetyConfig()
        audit_event = AuditEvent(
            event_id=str(uuid.uuid4()),
            job_id=payload.get("job_id", "unknown"),
            task_id=inp.task_id,
            role_type=self.role_type,
            proposed_tool_category=ToolCategory.research,
            action="proposed_tool_call",
            status=AuditStatus.pending,
            message=f"ResearchAgent requested file_metadata tool for path={path!r}",
        )
        output = inspect_file_metadata(
            task_id=inp.task_id,
            relative_path=path,
            safety_config=safety_config,
            audit_event=audit_event,
        )
        if output.success and not output.blocked:
            audit_event.status = AuditStatus.allowed
        else:
            audit_event.status = AuditStatus.blocked
        audit_event.message = output.error_message or "File metadata access granted"
        audit_event.timestamp = datetime.now(timezone.utc)
        try:
            store = StateStore()
            store.append_audit_event(audit_event.job_id, audit_event)
        except Exception:
            pass
        return AgentOutput(
            task_id=inp.task_id,
            role_type=self.role_type,
            result=output.to_agent_output()["result"],
            success=output.success,
            error_message=output.error_message,
        )


class MemoryStateAgent(BaseRole):
    name      = "MemoryStateAgent"
    role_type = RoleType.memory_state

    def run(self, inp: AgentInput) -> AgentOutput:
        ok, err = self._check_role_type(inp)
        if not ok:
            return self._failure(inp, err)
        operation = inp.payload.get("operation", "read")
        key       = inp.payload.get("key", "")
        return AgentOutput(
            task_id=inp.task_id,
            role_type=self.role_type,
            result={
                "operation": operation,
                "key":       key,
                "value":     f"[STUB] Memory op {operation!r} on key {key!r} not implemented",
            },
            success=True,
        )


class ExecutionAgent(BaseRole):
    name      = "ExecutionAgent"
    role_type = RoleType.execution

    def run(self, inp: AgentInput) -> AgentOutput:
        ok, err = self._check_role_type(inp)
        if not ok:
            return self._failure(inp, err)
        action = inp.payload.get("action", "")
        return AgentOutput(
            task_id=inp.task_id,
            role_type=self.role_type,
            result={
                "action":  action,
                "outcome": f"[STUB] Execution action {action!r} not implemented",
            },
            success=True,
        )
