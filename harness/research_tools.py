"""
Read-only research tools for Hermes Multi-Agent Harness v1.
"""
from __future__ import annotations
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

from pydantic import BaseModel
from harness.job_models import (
    AgentInput, AgentOutput, AuditEvent, AuditStatus, RoleType, SafetyConfig, ToolCategory,
)

HARNESS_ROOT = Path("/home/jfroh/hermes/harness/").resolve()

class ResearchMetadataOutput(BaseModel):
    success: bool
    blocked: bool
    error_message: Optional[str] = None
    data: Dict[str, Any] = {}

    @property
    def status(self) -> str:
        if self.success:
            return "granted"
        elif self.blocked:
            return "denied"
        else:
            return "error"

    @property
    def reason(self) -> str:
        return self.error_message or ""

    def __getitem__(self, key: str) -> Any:
        if key == "status":
            return self.status
        if key == "reason":
            return self.reason
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def to_agent_output(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "result": self.data if self.success else {},
            "error_message": self.error_message
        }

def inspect_file_metadata(task_id: str, relative_path: str, safety_config: SafetyConfig, audit_event: AuditEvent) -> ResearchMetadataOutput:
    # 1. Safety Gate: Deterministic Only
    if safety_config.deterministic_only:
        return ResearchMetadataOutput(success=False, blocked=True, error_message="Real tool access blocked: deterministic_only=True")
    
    # 2. Safety Gate: Real Tool Calls Allowed
    if not safety_config.allow_real_tool_calls:
        return ResearchMetadataOutput(success=False, blocked=True, error_message="Real tool access blocked: allow_real_tool_calls=False")
        
    # 3. Safety Gate: Category Allowlist
    if ToolCategory.research not in safety_config.allowed_tool_categories:
        return ResearchMetadataOutput(success=False, blocked=True, error_message="Real tool access blocked: Research category not allowed")

    # 4. Path Validation
    try:
        requested_path = (HARNESS_ROOT / relative_path).resolve()
        
        # Path traversal check
        if not str(requested_path).startswith(str(HARNESS_ROOT)):
            return ResearchMetadataOutput(success=False, blocked=False, error_message="Path traversal detected")
        
        # Restricted files (check by name and suffix, regardless of existence)
        blocked_suffixes = {'.env', '.key', '.pem', '.p12', '.json'}
        if requested_path.name.startswith('.') or requested_path.suffix in blocked_suffixes or requested_path.name == 'credentials.json':
            return ResearchMetadataOutput(success=False, blocked=False, error_message="Access denied: restricted file type")

        # Exists check
        if not requested_path.exists():
            return ResearchMetadataOutput(success=False, blocked=False, error_message="File does not exist")
        
        if requested_path.is_dir():
            return ResearchMetadataOutput(success=False, blocked=False, error_message="Directories not supported")

        # Gather metadata
        stat = requested_path.stat()
        return ResearchMetadataOutput(
            success=True, 
            blocked=False, 
            data={
                "exists": True,
                "resolved_path": str(requested_path),
                "size_bytes": stat.st_size,
                "extension": requested_path.suffix,
                "last_modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                "line_count": sum(1 for _ in requested_path.open('r', encoding='utf-8', errors='ignore'))
            }
        )
    except Exception as e:
        return ResearchMetadataOutput(success=False, blocked=False, error_message=str(e))
