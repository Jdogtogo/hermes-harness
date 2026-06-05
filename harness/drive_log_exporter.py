import json
from pathlib import Path
from datetime import datetime
import os

# Target folder
DRIVE_TARGET = Path("/mnt/h/My Drive/Hermes_Workspace/Live_Logs/")

class DriveLogExporter:
    def __init__(self, event_file: Path, output_dir: Path):
        self.event_file = event_file
        self.output_dir = output_dir

    def export(self):
        if not self.output_dir.exists():
            print(f"Warning: Drive target path not found: {self.output_dir}")
            return False

        if not self.event_file.exists():
            print(f"Error: Event file not found: {self.event_file}")
            return False

        events = []
        try:
            with open(self.event_file, 'r') as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))
        except Exception as e:
            print(f"Error reading events: {e}")
            return False

        # Exporter strategies
        self.export_status(events)
        self.export_rolling_log(events)
        return True

    def export_status(self, events):
        # Hermes_Live_Status.txt
        status_file = self.output_dir / "Hermes_Live_Status.txt"
        with open(status_file, 'w') as f:
            f.write(f"Hermes Live Status\n")
            f.write(f"Generated: {datetime.utcnow().isoformat()}\n")
            f.write(f"Event Count: {len(events)}\n")
            f.write(f"Status: Operational\n")

    def export_rolling_log(self, events):
        # Hermes_Event_Log_Rolling.txt (last 500)
        rolling_file = self.output_dir / "Hermes_Event_Log_Rolling.txt"
        with open(rolling_file, 'w') as f:
            for e in events[-500:]:
                # Allowlist safe fields
                safe_event = {
                    "timestamp": e.get("timestamp"),
                    "type": e.get("event_type"),
                    "severity": e.get("severity"),
                    "phase": e.get("phase"),
                    "adjudication": e.get("adjudication_decision"),
                    "human_required": e.get("human_required")
                }
                f.write(json.dumps(safe_event) + "\n")

def main():
    event_file = Path("events/harness_events.jsonl")
    exporter = DriveLogExporter(event_file, DRIVE_TARGET)
    if exporter.export():
        print("Drive export successful")
    else:
        print("Drive export failed or skipped")

if __name__ == "__main__":
    main()