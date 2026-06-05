import json
import pytest
from pathlib import Path
from harness.event_consumer import EventConsumer

def test_reads_valid_event_stream(tmp_path):
    event_file = tmp_path / "events.jsonl"
    event_file.write_text('{"event_type": "phase_started", "phase": "test", "severity": "info"}\n')
    consumer = EventConsumer(event_file)
    summary = consumer.get_dashboard_summary()
    assert summary["total_events"] == 1
    assert summary["event_types"]["phase_started"] == 1

def test_handles_empty_event_stream(tmp_path):
    event_file = tmp_path / "empty.jsonl"
    event_file.write_text('')
    consumer = EventConsumer(event_file)
    summary = consumer.get_dashboard_summary()
    assert summary["total_events"] == 0

def test_handles_malformed_line_safely(tmp_path):
    event_file = tmp_path / "malformed.jsonl"
    event_file.write_text('{"event_type": "valid"}\nINVALID_JSON\n{"event_type": "valid2"}\n')
    consumer = EventConsumer(event_file)
    summary = consumer.get_dashboard_summary()
    assert summary["total_events"] == 2

def test_counts_types_and_severities(tmp_path):
    event_file = tmp_path / "counts.jsonl"
    event_file.write_text('{"event_type": "A", "severity": "info"}\n{"event_type": "B", "severity": "info"}\n{"event_type": "A", "severity": "error"}\n')
    consumer = EventConsumer(event_file)
    summary = consumer.get_dashboard_summary()
    assert "A" in summary["event_types"]
    assert summary["event_types"]["A"] == 2
    assert "B" in summary["event_types"]
    assert summary["event_types"]["B"] == 1
    assert "info" in summary["severities"]
    assert summary["severities"]["info"] == 2
    assert "error" in summary["severities"]
    assert summary["severities"]["error"] == 1

def test_detects_human_required(tmp_path):
    event_file = tmp_path / "human.jsonl"
    event_file.write_text('{"human_required": false}\n{"human_required": true}\n')
    consumer = EventConsumer(event_file)
    summary = consumer.get_dashboard_summary()
    assert summary["human_required"] is True

def test_no_exposure_of_sensitive_data(tmp_path):
    event_file = tmp_path / "secret.jsonl"
    event_file.write_text('{"event_type": "A", "secret": "token123", "token": "abc", "password": "123"}\n')
    consumer = EventConsumer(event_file)
    summary = consumer.get_dashboard_summary()
    last = summary["last_10_summaries"][0]
    assert isinstance(last, dict)
    assert set(last.keys()) == {"timestamp", "type", "phase"}
