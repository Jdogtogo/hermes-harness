import json
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Literal, Optional, Dict, Set, Any
from jsonschema import validate, ValidationError

# --- Schemas ---
# Note: For simplicity, we define these schemas inline.
# In a full-scale app, they would be external files.

PROPOSED_ACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "action_type": {"type": "string", "enum": [
            "read_file", "write_file", "patch_file", "delete_file", "shell", "python",
            "web_read", "download", "external_message", "api_write", "credential_access",
            "financial_action", "cron_job", "spawn_agent", "git_commit", "git_push",
            "memory_write", "report_write", "adjudicator_manifest_update"
        ]},
        "paths": {"type": "array", "items": {"type": "string"}},
        "command": {"type": ["string", "null"]},
        "target": {"type": ["string", "null"]},
        "bytes_expected": {"type": ["number", "null"]},
        "reason": {"type": "string"}
    },
    "required": ["action_type", "reason"]
}

TASK_POLICY_SCHEMA = {
    "type": "object",
    "properties": {
        "task_id": {"type": "string"},
        "risk_class": {"type": "string", "enum": ["Green", "Amber", "Orange", "Red", "Black"]},
        "allowed_write_paths": {"type": "array", "items": {"type": "string"}},
        "allowed_read_roots": {"type": "array", "items": {"type": "string"}},
        "denied_write_roots": {"type": "array", "items": {"type": "string"}},
        "denied_read_roots": {"type": "array", "items": {"type": "string"}},
        "allowed_command_patterns": {"type": "array", "items": {"type": "string"}},
        "denied_command_patterns": {"type": "array", "items": {"type": "string"}},
        "external_write_allowed": {"type": "boolean"},
        "credential_access_allowed": {"type": "boolean"},
        "financial_action_allowed": {"type": "boolean"},
        "cron_allowed": {"type": "boolean"},
        "spawn_agent_allowed": {"type": "boolean"},
        "large_download_limit_mb": {"type": "number"},
        "mode": {"type": "string", "enum": ["plan_only", "dry_run", "act", "report_correction_only", "complete"]},
        "manifest_locked": {"type": "boolean"},
        "manifest_phase": {"type": "string", "enum": ["preflight", "act", "verification"]},
        "manifest_path": {"type": ["string", "null"]},
        "evidence_report_path": {"type": ["string", "null"]}
    },
    "required": [
        "task_id", "risk_class", "allowed_write_paths", "allowed_read_roots",
        "denied_write_roots", "denied_read_roots", "allowed_command_patterns",
        "denied_command_patterns", "external_write_allowed", "credential_access_allowed",
        "financial_action_allowed", "cron_allowed", "spawn_agent_allowed",
        "large_download_limit_mb", "mode", "manifest_locked", "manifest_phase"
    ]
}

LOOP_STATE_SCHEMA = {
    "type": "object",
    "properties": {
        "implementation_attempts": {"type": "number"},
        "verification_fix_cycles": {"type": "number"},
        "report_corrections": {"type": "number"},
        "risk_increased": {"type": "boolean"}
    },
    "required": ["implementation_attempts", "verification_fix_cycles", "report_corrections", "risk_increased"]
}

# --- Data Structures ---

@dataclass
class ProposedAction:
    action_type: str
    paths: List[Path] = field(default_factory=list)
    command: Optional[str] = None
    target: Optional[str] = None
    bytes_expected: Optional[int] = None
    reason: str = ''

@dataclass
class TaskPolicy:
    task_id: str
    risk_class: str
    allowed_write_paths: Set[Path]
    allowed_read_roots: Set[Path]
    denied_write_roots: Set[Path]
    denied_read_roots: Set[Path]
    allowed_command_patterns: List[str]
    denied_command_patterns: List[str]
    external_write_allowed: bool
    credential_access_allowed: bool
    financial_action_allowed: bool
    cron_allowed: bool
    spawn_agent_allowed: bool
    large_download_limit_mb: float
    mode: str
    manifest_locked: bool
    manifest_phase: str
    manifest_path: Optional[Path] = None
    evidence_report_path: Optional[Path] = None

@dataclass
class LoopState:
    implementation_attempts: int
    verification_fix_cycles: int
    report_corrections: int
    risk_increased: bool

# --- Gate Evaluator ---

def validate_input(action_data: Any, policy_data: Any, loop_data: Any):
    try:
        if not isinstance(action_data, dict): return False, "RULE_INVALID_INPUT_TYPE"
        validate(instance=action_data, schema=PROPOSED_ACTION_SCHEMA)
        
        if not isinstance(policy_data, dict): return False, "RULE_INVALID_INPUT_TYPE"
        validate(instance=policy_data, schema=TASK_POLICY_SCHEMA)
        
        if not isinstance(loop_data, dict): return False, "RULE_INVALID_INPUT_TYPE"
        validate(instance=loop_data, schema=LOOP_STATE_SCHEMA)
    except ValidationError as e:
        return False, f"RULE_SCHEMA_VALIDATION_FAILED: {e.message}"
    except Exception as e:
        return False, f"RULE_UNKNOWN_VALIDATION_ERROR: {str(e)}"
    return True, None

def matches_any(text, patterns):
    for p in patterns:
        if p in text: return True
    return False

def resolve_path(p: Path):
    try:
        if p.exists() and p.is_symlink():
            return p.resolve()
    except Exception:
        pass
    return p.resolve()

def gate(action_dict: Dict, policy_dict: Dict, loop_dict: Dict):
    # Rule: Schema Validation
    is_valid, error_msg = validate_input(action_dict, policy_dict, loop_dict)
    if not is_valid:
        return "deny", error_msg

    # Convert to objects
    action = ProposedAction(
        action_type=action_dict['action_type'],
        paths=[Path(p) for p in action_dict.get('paths', [])],
        command=action_dict.get('command'),
        target=action_dict.get('target'),
        bytes_expected=action_dict.get('bytes_expected'),
        reason=action_dict['reason']
    )
    policy = TaskPolicy(
        task_id=policy_dict['task_id'],
        risk_class=policy_dict['risk_class'],
        allowed_write_paths={Path(p) for p in policy_dict['allowed_write_paths']},
        allowed_read_roots={Path(p) for p in policy_dict['allowed_read_roots']},
        denied_write_roots={Path(p) for p in policy_dict['denied_write_roots']},
        denied_read_roots={Path(p) for p in policy_dict['denied_read_roots']},
        allowed_command_patterns=policy_dict['allowed_command_patterns'],
        denied_command_patterns=policy_dict['denied_command_patterns'],
        external_write_allowed=policy_dict['external_write_allowed'],
        credential_access_allowed=policy_dict['credential_access_allowed'],
        financial_action_allowed=policy_dict['financial_action_allowed'],
        cron_allowed=policy_dict['cron_allowed'],
        spawn_agent_allowed=policy_dict['spawn_agent_allowed'],
        large_download_limit_mb=policy_dict['large_download_limit_mb'],
        mode=policy_dict['mode'],
        manifest_locked=policy_dict['manifest_locked'],
        manifest_phase=policy_dict['manifest_phase'],
        manifest_path=Path(policy_dict['manifest_path']) if policy_dict.get('manifest_path') else None,
        evidence_report_path=Path(policy_dict['evidence_report_path']) if policy_dict.get('evidence_report_path') else None
    )
    state = LoopState(
        implementation_attempts=loop_dict['implementation_attempts'],
        verification_fix_cycles=loop_dict['verification_fix_cycles'],
        report_corrections=loop_dict['report_corrections'],
        risk_increased=loop_dict['risk_increased']
    )

    # Rule: Manifest Immutability
    if policy.manifest_locked:
        if action.action_type in ['write_file', 'patch_file', 'delete_file', 'report_write'] and \
           policy.manifest_path and any(policy.manifest_path == resolve_path(p) for p in action.paths):
            return "deny", "RULE_MANIFEST_LOCKED_NO_POLICY_EXPANSION"
        
    if policy.manifest_phase == 'act' and action.action_type == 'write_file' and \
       policy.manifest_path and any(policy.manifest_path == resolve_path(p) for p in action.paths):
        return "deny", "RULE_MANIFEST_LOCKED_NO_POLICY_EXPANSION"

    # Rule 1: Black risk
    if policy.risk_class == 'Black':
        return "deny", "RULE_BLACKLISTED_RISK_CLASS"

    # Rule 2: Financial/Client-Sensitive
    if action.action_type == 'financial_action':
        return "require_human", "RULE_FINANCIAL_ACTION_REQUIRES_HUMAN"

    # Rule 3: External Side Effects
    if action.action_type in ['external_message', 'api_write'] and not policy.external_write_allowed:
        return "deny", "RULE_EXTERNAL_ACTION_NOT_ALLOWED"

    # Rule 4: Credential access
    if action.action_type == 'credential_access' and not policy.credential_access_allowed:
        return "deny", "RULE_CREDENTIAL_ACCESS_NOT_ALLOWED"

    # Rule 5: Cron/Spawn
    if action.action_type in ['cron_job', 'spawn_agent']:
        if action.action_type == 'cron_job' and not policy.cron_allowed:
            return "deny", "RULE_CRON_NOT_ALLOWED"
        if action.action_type == 'spawn_agent' and not policy.spawn_agent_allowed:
            return "deny", "RULE_SPAWN_AGENT_NOT_ALLOWED"
        return "require_human", "RULE_PERSISTENT_TASK_REQUIRES_APPROVAL"

    # Rule 6: Path Enforcement
    protected_roots = {
        Path("/home/jfroh/.hermes/secrets/"),
        Path("/home/jfroh/.hermes/.env/"),
        Path("/home/jfroh/.ssh/"),
        Path("/mnt/c/Users/jfroh/.ssh/"),
        Path("/home/jfroh/.hermes/hermes-agent/"),
        Path("/home/jfroh/.hermes/cron/")
    }

    if action.action_type in ['read_file', 'write_file', 'patch_file', 'delete_file', 'memory_write']:
        for p in action.paths:
            if not p.is_absolute():
                return "deny", f"RULE_RELATIVE_PATH_NOT_ALLOWED"
            
            resolved = resolve_path(p)

            # Check protected roots
            if any(resolved.is_relative_to(root) for root in protected_roots):
                return "deny", f"RULE_ACCESS_TO_PROTECTED_ROOT"

            # Denied roots
            if any(resolved.is_relative_to(root) for root in policy.denied_write_roots):
                return "deny", f"RULE_DENIED_ROOT"
            if action.action_type == 'read_file' and any(resolved.is_relative_to(root) for root in policy.denied_read_roots):
                return "deny", f"RULE_DENIED_READ_ROOT"

            # Check allowed paths
            if action.action_type in ['write_file', 'patch_file', 'delete_file', 'memory_write']:
                if not any(resolved.is_relative_to(allowed) for allowed in policy.allowed_write_paths):
                    return "deny", f"RULE_PATH_OUTSIDE_ALLOWED_WRITE_PATH"
            
            if action.action_type == 'read_file':
                if not any(resolved.is_relative_to(allowed) for allowed in policy.allowed_read_roots):
                    return "deny", f"RULE_PATH_OUTSIDE_ALLOWED_READ_ROOTS"
                    
            if action.action_type == 'delete_file':
                return "require_human", "RULE_DELETE_REQUIRES_HUMAN_APPROVAL"

    # Rule 7: Shell/Python Commands
    if action.action_type in ['shell', 'python']:
        if matches_any(action.command or '', policy.denied_command_patterns):
            return "deny", f"RULE_DENIED_COMMAND_PATTERN"

    # Rule 8: Mode Restrictions
    if policy.mode == 'plan_only' and action.action_type in ['write_file', 'patch_file', 'delete_file']:
        return "deny", "RULE_PLAN_ONLY_MODE_DENIES_WRITE"
    if policy.mode == 'report_correction_only' and action.action_type not in ['report_write']:
        return "deny", "RULE_REPORT_CORRECTION_ONLY_MODE_DENIES_NON_REPORT_ACTIONS"

    # Rule 9: Loop Limits
    if state.implementation_attempts > 2:
        return "lock_task", "RULE_LOOP_LIMIT_EXCEEDED"
    if state.verification_fix_cycles > 2:
        return "lock_task", "RULE_LOOP_LIMIT_EXCEEDED"

    # Rule 10: Large download
    if action.action_type == 'download':
        if (action.bytes_expected or 0) > (policy.large_download_limit_mb * 1024 * 1024):
            return "require_human", "RULE_LARGE_DOWNLOAD_LIMIT_EXCEEDED"

    return "allow", "within policy"
