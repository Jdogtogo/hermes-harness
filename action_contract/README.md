# Action Contract V0 Validator

This directory contains the strict typed Action Contract validator for the Execution Governor.
V0 Contract Requirements:
- Structural validation against `action_contract.schema.yaml`
- Deterministic outcome: `ACTION_CONTRACT_VALID`, `ACTION_CONTRACT_INVALID`, `ACTION_CONTRACT_ESCALATE`
- Enforcement of safety boundaries (e.g., no git push, no memory writes in V0).
