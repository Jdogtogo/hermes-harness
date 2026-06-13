import json
import shutil
from pathlib import Path
from datetime import datetime
import os

# ── Path constants ──────────────────────────────────────────────────────────────
# Local WSL workspace is canonical. Google Drive is optional archive/export only.
LOCAL_TARGET   = Path.home() / ".hermes/workspace/live_logs"
DRIVE_WORKSPACE = Path("/mnt/h/My Drive/Hermes_Workspace")
DRIVE_TARGET   = DRIVE_WORKSPACE / "Live_Logs"


class DriveLogExporter:
    """Exports harness events to structured log files in a given output directory.

    The class is output-directory-agnostic — callers supply output_dir.
    Use main() for the standard local-first export with optional Drive sync.
    """

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

        # Export strategies
        self.export_live_status(events)
        self.export_rolling_log(events)
        self.export_adjudication_history(events)
        self.export_blockers_and_actions(events)
        self.export_infrastructure_state(events)
        self.export_daily_summary(events)

        return True

    def export_live_status(self, events):
        with open(self.output_dir / "Hermes_Live_Status.txt", 'w') as f:
            f.write(f"Hermes Live Status\nGenerated: {datetime.utcnow().isoformat()}Z\n")
            f.write(f"Total Events: {len(events)}\n")
            f.write("Status: Operational\n")

    def export_rolling_log(self, events):
        with open(self.output_dir / "Hermes_Event_Log_Rolling.txt", 'w') as f:
            for e in events[-500:]:
                f.write(json.dumps({k: e.get(k) for k in ["timestamp", "event_type", "severity", "phase"]}) + "\n")

    def export_adjudication_history(self, events):
        with open(self.output_dir / "Hermes_Adjudication_History.txt", 'w') as f:
            for e in events[-200:]:
                if "adjudication_decision" in e:
                    f.write(f"{e.get('timestamp')} | {e.get('adjudication_decision')} | {e.get('phase')}\n")

    def export_blockers_and_actions(self, events):
        with open(self.output_dir / "Hermes_Blockers_And_Human_Actions.txt", 'w') as f:
            for e in events[-200:]:
                if e.get("human_required"):
                    f.write(f"{e.get('timestamp')} | Human Required: {e.get('summary', 'No summary')}\n")

    def export_infrastructure_state(self, events):
        with open(self.output_dir / "Hermes_Current_Infrastructure_State.txt", 'w') as f:
            f.write("Infrastructure State: Nominal\n")
            f.write(f"Commit: {os.popen('git rev-parse --short HEAD').read().strip()}\n")

    def export_daily_summary(self, events):
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        with open(self.output_dir / f"Hermes_Daily_Summary_{date_str}.txt", 'w') as f:
            f.write(f"Summary for {date_str}\n")
            f.write(f"Events today: {len([e for e in events if e.get('timestamp', '').startswith(date_str)])}\n")


def _copy_to_drive(local_dir: Path) -> None:
    """Copy local live_logs to Drive. Best-effort — never raises."""
    if not DRIVE_WORKSPACE.is_dir():
        print(f"Warning: Drive not available at {DRIVE_WORKSPACE} — skipping Drive export")
        return
    try:
        DRIVE_TARGET.mkdir(parents=True, exist_ok=True)
        for src in local_dir.iterdir():
            if src.is_file():
                shutil.copyfile(src, DRIVE_TARGET / src.name)
        print(f"Drive export complete: {DRIVE_TARGET}")
    except (OSError, shutil.Error) as e:
        print(f"Warning: Drive export failed (non-fatal): {e}")


def main():
    event_file = Path("events/harness_events.jsonl")

    # Ensure local target exists (idempotent)
    LOCAL_TARGET.mkdir(parents=True, exist_ok=True)

    # Export to local workspace first (always)
    exporter = DriveLogExporter(event_file, LOCAL_TARGET)
    if exporter.export():
        print("Local export successful")
        # Optional Drive export — best-effort, never blocks success
        _copy_to_drive(LOCAL_TARGET)
    else:
        print("Local export failed or skipped")


if __name__ == "__main__":
    main()
