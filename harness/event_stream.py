from __future__ import annotations
import json
import uuid
import os
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, field_validator

class EventType(str, Enum):
    PHASE_STARTED = "phase_started"
    VERIFICATION_STARTED = "verification_started"
    VERIFICATION_PASSED = "verification_passed"
    VERIFICATION_FAILED = "verification_failed"
    ADJUDICATION_REQUESTED = "adjudication_requested"
    ADJUDICATION_APPROVED = "adjudication_approved"
    ADJUDICATION_REJECTED = "adjudication_rejected"
    MANUAL_GATE_WAITING = "manual_gate_waiting"
    PHASE_COMPLETED = "phase_completed"
    PHASE_BLOCKED = "phase_blocked"

class EventSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class HarnessEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: EventType
    phase: str
    status: str
    severity: EventSeverity
    source: str = "harness-v1-baseline"
    git_commit: str = "437ba92"
    report_path: Optional[str] = None
    adjudication_decision: Optional[str] = None
    next_action: Optional[str] = None
    human_required: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('metadata')
    @classmethod
    def check_secrets(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        forbidden = {'token', 'key', 'password', 'secret', 'credential', 'api_key'}
        for key in v.keys():
            if any(f in key.lower() for f in forbidden):
                raise ValueError(f"Metadata key {key} contains forbidden sensitive pattern")
        return v

class EventWriter:
    def __init__(self, log_path: Path = Path("/home/jfroh/hermes/harness/events/harness_events.jsonl")):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: HarnessEvent):
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(event.model_dump_json() + "\n")
