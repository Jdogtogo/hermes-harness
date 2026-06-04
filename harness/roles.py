"""
Minimal role abstractions for Hermes Multi-Agent Harness v1.
"""
from __future__ import annotations

from harness.job_models import (
    AgentInput, AgentOutput, RoleType, SafetyConfig, ToolCategory,
)
from harness.research_tools import inspect_file_metadata


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

        tool = inp.payload.get("tool")

        if tool == "inspect_file_metadata":
            return self._run_metadata_tool(inp)

        # Default deterministic stub — no real tool calls.
        query = inp.payload.get("query", "")
        return AgentOutput(
            task_id=inp.task_id,
            role_type=self.role_type,
            result={
                "query":    query,
                "findings": f"[STUB] No real research performed for: {query!r}",
            },
            success=True,
        )

    def _run_metadata_tool(self, inp: AgentInput) -> AgentOutput:
        """Defence-in-depth gate before calling inspect_file_metadata."""
        cfg: SafetyConfig | None = inp.safety_config

        if cfg is None:
            return self._failure(inp, "Metadata tool blocked: no SafetyConfig provided")
        if cfg.deterministic_only:
            return self._failure(
                inp,
                "Metadata tool blocked: SafetyConfig.deterministic_only is True",
            )
        if not cfg.allow_real_tool_calls:
            return self._failure(
                inp,
                "Metadata tool blocked: SafetyConfig.allow_real_tool_calls is False",
            )
        if ToolCategory.research not in cfg.allowed_tool_categories:
            return self._failure(
                inp,
                "Metadata tool blocked: ToolCategory.research not in allowed_tool_categories",
            )
        if cfg.require_audit_log and not inp.has_audit_context:
            return self._failure(
                inp,
                "Metadata tool blocked: audit context required but not present",
            )

        path: str = inp.payload.get("path", "")
        meta = inspect_file_metadata(path)

        if meta.get("status") == "denied":
            return AgentOutput(
                task_id=inp.task_id,
                role_type=self.role_type,
                result=meta,
                success=False,
                error_message=f"inspect_file_metadata denied: {meta.get('reason', '')}",
            )

        return AgentOutput(
            task_id=inp.task_id,
            role_type=self.role_type,
            result=meta,
            success=True,
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
