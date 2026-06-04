"""
Minimal role abstractions for Hermes Multi-Agent Harness v1.

ResearchAgent, MemoryStateAgent, ExecutionAgent are deterministic,
non-LLM placeholder implementations.  Each validates I/O against the
Harness schemas and returns an honest [STUB] marker so callers know
no real work has been performed.

These are NOT autonomous LLM agents.  They are safe, testable foundations.
"""
from __future__ import annotations

from harness.job_models import AgentInput, AgentOutput, RoleType


class BaseRole:
    name:      str      = "BaseRole"
    role_type: RoleType

    # ── input validation ───────────────────────────────────────────────────

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


# ── ResearchAgent ──────────────────────────────────────────────────────────

class ResearchAgent(BaseRole):
    """
    Placeholder research role.

    Input payload:  {"query": str}
    Output result:  {"query": str, "findings": str}
    """
    name      = "ResearchAgent"
    role_type = RoleType.research

    def run(self, inp: AgentInput) -> AgentOutput:
        ok, err = self._check_role_type(inp)
        if not ok:
            return self._failure(inp, err)
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


# ── MemoryStateAgent ───────────────────────────────────────────────────────

class MemoryStateAgent(BaseRole):
    """
    Placeholder memory/state role.

    Input payload:  {"operation": "read"|"write", "key": str, "value": any}
    Output result:  {"operation": str, "key": str, "value": str}
    """
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


# ── ExecutionAgent ─────────────────────────────────────────────────────────

class ExecutionAgent(BaseRole):
    """
    Placeholder execution role.

    Input payload:  {"action": str}
    Output result:  {"action": str, "outcome": str}
    """
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
