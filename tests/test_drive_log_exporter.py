import json
import os
import tempfile
from pathlib import Path
import sys

# Add the harness directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from harness.drive_log_exporter import DriveLogExporter

def test_drive_exporter_success():
    """Test that all expected files are written when the target directory exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = Path(tmpdir) / "Live_Logs"
        target_dir.mkdir()
        
        event_file = Path(tmpdir) / "events.jsonl"
        with open(event_file, 'w') as f:
            f.write(json.dumps({"timestamp": "2026-06-05T10:00:00Z", "event_type": "test", "adjudication_decision": "approved", "human_required": True}) + '\n')
            
        exporter = DriveLogExporter(event_file, target_dir)
        success = exporter.export()
        assert success is True
        
        assert (target_dir / "Hermes_Live_Status.txt").exists()
        assert (target_dir / "Hermes_Event_Log_Rolling.txt").exists()
        assert (target_dir / "Hermes_Adjudication_History.txt").exists()
        assert (target_dir / "Hermes_Blockers_And_Human_Actions.txt").exists()
        assert (target_dir / "Hermes_Current_Infrastructure_State.txt").exists()
        
        # Check daily summary file
        from datetime import datetime
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        assert (target_dir / f"Hermes_Daily_Summary_{date_str}.txt").exists()

def test_drive_exporter_fail_gracefully():
    """Test that it fails gracefully when target directory does not exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        non_existent_dir = Path(tmpdir) / "DoesNotExist"
        event_file = Path(tmpdir) / "events.jsonl"
        
        exporter = DriveLogExporter(event_file, non_existent_dir)
        success = exporter.export()
        assert success is False

def test_drive_exporter_capping():
    """Test that the rolling log is capped."""
    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = Path(tmpdir) / "Live_Logs"
        target_dir.mkdir()
        
        event_file = Path(tmpdir) / "events.jsonl"
        with open(event_file, 'w') as f:
            for i in range(600):
                f.write(json.dumps({"timestamp": "2026-06-05T10:00:00Z"}) + '\n')
        
        exporter = DriveLogExporter(event_file, target_dir)
        exporter.export()
        
        rolling_file = target_dir / "Hermes_Event_Log_Rolling.txt"
        lines = rolling_file.read_text().splitlines()
        assert len(lines) <= 500

if __name__ == "__main__":
    test_drive_exporter_success()
    test_drive_exporter_fail_gracefully()
    test_drive_exporter_capping()
    print("Drive exporter tests passed!")