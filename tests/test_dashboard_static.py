import json
import os
import tempfile
from pathlib import Path
import sys

# Add the harness directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from harness.dashboard_static import DashboardGenerator

def test_dashboard_generation():
    """Test that the dashboard generator creates an HTML file with expected content."""
    # Create a temporary event file with some sample data
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        # Write a few sample events
        events = [
            {
                "timestamp": "2026-06-05T10:00:00Z",
                "event_type": "verification_started",
                "phase": "1",
                "severity": "info",
                "adjudication_decision": "pending",
                "human_required": False,
                "summary": "Verification started"
            },
            {
                "timestamp": "2026-06-05T10:05:00Z",
                "event_type": "manual_gate_waiting",
                "phase": "2",
                "severity": "warning",
                "adjudication_decision": "approved",
                "human_required": True,
                "summary": "Waiting for human approval"
            }
        ]
        for event in events:
            f.write(json.dumps(event) + '\n')
        temp_event_file = f.name

    try:
        generator = DashboardGenerator(Path(temp_event_file))
        summary = generator.get_dashboard_summary()
        html_output = generator.generate_html(summary)

        # Check that the HTML output contains expected sections
        assert "<!DOCTYPE html>" in html_output
        assert "<h1>Hermes Harness Dashboard</h1>" in html_output
        assert "Current Harness Status" in html_output
        assert "Event Counts by Type" in html_output
        assert "Severity Counts" in html_output
        assert "Last 10 Events" in html_output
        assert "Repository Info" in html_output

        # Check that the data is present
        assert "2" in html_output  # total events
        assert "verification_started" in html_output
        assert "manual_gate_waiting" in html_output
        assert "info" in html_output
        assert "warning" in html_output
        assert "2026-06-05T10:00:00Z" in html_output
        assert "2026-06-05T10:05:00Z" in html_output

    finally:
        os.unlink(temp_event_file)

def test_empty_event_stream():
    """Test that the dashboard handles an empty event stream."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        temp_event_file = f.name

    try:
        generator = DashboardGenerator(Path(temp_event_file))
        summary = generator.get_dashboard_summary()
        html_output = generator.generate_html(summary)

        # Check that the total events value is 0
        assert 'Total Events' in html_output
        import re
        pattern = r"<div class='data-item'>\s*<div class='label'>Total Events</div>\s*<div class='value'>(\d+)</div>"
        match = re.search(pattern, html_output)
        assert match is not None
        assert match.group(1) == '0'
    finally:
        os.unlink(temp_event_file)

def test_malformed_event_lines():
    """Test that malformed JSON lines are skipped."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write('{"timestamp": "2026-06-05T10:00:00Z", "event_type": "test"}\n')
        f.write('not json\n')
        f.write('{"timestamp": "2026-06-05T10:05:00Z", "event_type": "test2"}\n')
        temp_event_file = f.name

    try:
        generator = DashboardGenerator(Path(temp_event_file))
        summary = generator.get_dashboard_summary()
        assert summary['total_events'] == 2
        html_output = generator.generate_html(summary)
        assert "test" in html_output
        assert "test2" in html_output
    finally:
        os.unlink(temp_event_file)

def test_no_launch_buttons_or_forms():
    """Test that the generated HTML does not contain launch buttons or forms."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        events = [
            {
                "timestamp": "2026-06-05T10:00:00Z",
                "event_type": "verification_started",
                "phase": "1",
                "severity": "info",
                "adjudication_decision": "pending",
                "human_required": False,
                "summary": "Verification started"
            }
        ]
        for event in events:
            f.write(json.dumps(event) + '\n')
        temp_event_file = f.name

    try:
        generator = DashboardGenerator(Path(temp_event_file))
        summary = generator.get_dashboard_summary()
        html_output = generator.generate_html(summary)

        assert "<button" not in html_output.lower()
        assert "<form" not in html_output.lower()
        assert "type=\"submit\"" not in html_output.lower()
        assert "onclick" not in html_output.lower()
    finally:
        os.unlink(temp_event_file)

def test_module_entry_point():
    """Test module entry point."""
    from harness.dashboard_static import main
    assert callable(main)

    with tempfile.TemporaryDirectory() as tmpdir:
        event_file = Path(tmpdir) / "events" / "harness_events.jsonl"
        event_file.parent.mkdir(parents=True, exist_ok=True)
        with open(event_file, 'w') as f:
            f.write(json.dumps({
                "timestamp": "2026-06-05T10:00:00Z",
                "event_type": "verification_started",
                "phase": "1",
                "severity": "info",
                "adjudication_decision": "pending",
                "human_required": False,
                "summary": "Verification started"
            }) + '\n')

        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            generator = DashboardGenerator(event_file)
            summary = generator.get_dashboard_summary()
            html_output = generator.generate_html(summary)
            assert "verification_started" in html_output
        finally:
            os.chdir(old_cwd)

if __name__ == "__main__":
    test_dashboard_generation()
    test_empty_event_stream()
    test_malformed_event_lines()
    test_no_launch_buttons_or_forms()
    test_module_entry_point()
    print("All tests passed!")