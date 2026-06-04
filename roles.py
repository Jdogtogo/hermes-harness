"""
Minimal role abstractions for Hermes Multi-Agent Harness v1.

ResearchAgent, MemoryStateAgent, ExecutionAgent are structural placeholders
with deterministic (non-LLM) implementations.  They validate I/O against
the Harness schemas and return honest STUB markers so callers know the
real logic has not been wired up yet.

These are NOT autonomous LLM agents.  They are safe, testable foundations.
"""

from __future__ import annotations

from schema import AgentInput, AgentOutput, RoleType


class BaseRole:
    """Common behaviour shared by all role implementations."""

    name: str = "BaseRole"
    role_type: RoleType

    def _validate_input(self, agent_input: AgentInput) -> tuple[bool, str]:
        if agent_input.role_type != self.role_type:
            return (
                False,
                f"Role mismatch: {self.name} expects {self.role_type}, "
                f"received {agent_input.role_type}",
            )
        return True, ""

    def _failure(self, agent_input: AgentInput, message: str) -> AgentOutput:
        return AgentOutput(
            task_id=agent_input.task_id,
            role_type=agent_input.role_type,
            result={},
            success=False,
            error_message=message,
        )

    def run(self, agent_input: AgentInput) -> AgentOutput:
        raise NotImplementedError(f"{self.name}.run() is not implemented")


# ---------------------------------------------------------------------------
# Research Agent
# ---------------------------------------------------------------------------

class ResearchAgent(BaseRole):
    """
    Structural placeholder for a future research role.

    Accepted input payload keys:
      - query (str): the research question

    Output result keys:
      - query (str): echoed back
      - findings (str): STUB message
    """

    name = "ResearchAgent"
    role_type = RoleType.research

    def run(self, agent_input: AgentInput) -> AgentOutput:
        valid, err = self._validate_input(agent_input)
        if not valid:
            return self._failure(agent_input, err)

        query = agent_input.payload.get("query", "")
        return AgentOutput(
            task_id=agent_input.task_id,
            role_type=self.role_type,
            result={
                "query": query,
                "findings": f"[STUB] No real research performed for: {query!r}",
            },
            success=True,
        )


# ---------------------------------------------------------------------------
# Memory / State Agent
# ---------------------------------------------------------------------------

class MemoryStateAgent(BaseRole):
    """
    Structural placeholder for a future memory/state role.

    Accepted input payload keys:
      - operation (str): 'read' or 'write'
      - key (str): the memory key
      - value (any, optional): value for write operations

    Output result keys:
      - operation (str)
      - key (str)
      - value (str): STUB message
    """

    name = "MemoryStateAgent"
    role_type = RoleType.memory_state

    def run(self, agent_input: AgentInput) -> AgentOutput:
        valid, err = self._validate_input(agent_input)
        if not valid:
            return self._failure(agent_input, err)

        operation = agent_input.payload.get("operation", "read")
        key = agent_input.payload.get("key", "")
        return AgentOutput(
            task_id=agent_input.task_id,
            role_type=self.role_type,
            result={
                "operation": operation,
                "key": key,
                "value": (
                    f"[STUB] Memory operation '{operation}' on key {key!r} "
                    "is not yet implemented"
                ),
            },
            success=True,
        )


# ---------------------------------------------------------------------------
# Execution Agent
# ---------------------------------------------------------------------------

class ExecutionAgent(BaseRole):
    """
    Structural placeholder for a future execution role.

    Accepted input payload keys:
      - action (str): the action to execute

    Output result keys:
      - action (str)
      - outcome (str): STUB message
    """

    name = "ExecutionAgent"
    role_type = RoleType.execution

    def run(self, agent_input: AgentInput) -> AgentOutput:
        valid, err = self._validate_input(agent_input)
        if not valid:
            return self._failure(agent_input, err)

        action = agent_input.payload.get("action", "")
        return AgentOutput(
            task_id=agent_input.task_id,
            role_type=self.role_type,
            result={
                "action": action,
                "outcome": (
                    f"[STUB] Execution action {action!r} is not yet implemented"
                ),
            },
            success=True,
        )
