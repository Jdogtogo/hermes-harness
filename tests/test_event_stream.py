import pytest
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from harness.event_stream import HarnessEvent, EventType, EventSeverity, EventWriter
from pydantic import ValidationError

def test_event_model_validates():
    event = HarnessEvent(
        event_type=EventType.PHASE_STARTED,
        phase="pilot",
        status="active",
        severity=EventSeverity.INFO
    )
    assert event.event_id is not None
    assert event.timestamp.tzinfo == timezone.utc

def test_timestamp_is_utc():
    event = HarnessEvent(
        event_type=EventType.PHASE_STARTED,
        phase="pilot",
        status="active",
        severity=EventSeverity.INFO
    )
    assert event.timestamp.tzinfo == timezone.utc

def test_event_writer_append():
    log_path = Path("/home/jfroh/hermes/harness/events/test_events.jsonl")
    if log_path.exists():
        log_path.unlink()
    
    writer = EventWriter(log_path=log_path)
    event = HarnessEvent(
        event_type=EventType.PHASE_STARTED,
        phase="pilot",
        status="active",
        severity=EventSeverity.INFO
    )
    writer.append(event)
    
    with open(log_path, "r") as f:
        lines = f.readlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["event_type"] == "phase_started"

def test_event_writer_append_preserves_order():
    log_path = Path("/home/jfroh/hermes/harness/events/test_events_order.jsonl")
    if log_path.exists():
        log_path.unlink()
    
    writer = EventWriter(log_path=log_path)
    writer.append(HarnessEvent(event_type=EventType.PHASE_STARTED, phase="1", status="ok", severity=EventSeverity.INFO))
    writer.append(HarnessEvent(event_type=EventType.PHASE_COMPLETED, phase="1", status="ok", severity=EventSeverity.INFO))
    
    with open(log_path, "r") as f:
        lines = f.readlines()
        assert len(lines) == 2
        assert json.loads(lines[0])["event_type"] == "phase_started"
        assert json.loads(lines[1])["event_type"] == "phase_completed"

def test_secret_metadata_rejected():
    with pytest.raises(ValidationError, match="forbidden sensitive pattern"):
        HarnessEvent(
            event_type=EventType.PHASE_STARTED,
            phase="pilot",
            status="active",
            severity=EventSeverity.INFO,
            metadata={"api_key": "supersecret"}
        )

def test_invalid_event_type_rejected():
    with pytest.raises(ValidationError):
        HarnessEvent(
            event_type="invalid_type",
            phase="pilot",
            status="active",
            severity=EventSeverity.INFO
        )

def test_invalid_severity_rejected():
    with pytest.raises(ValidationError):
        HarnessEvent(
            event_type=EventType.PHASE_STARTED,
            phase="pilot",
            status="active",
            severity="extreme"
        )
