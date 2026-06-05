import html
import json
from pathlib import Path
from collections import Counter
from datetime import datetime

class DashboardGenerator:
    def __init__(self, event_file: Path):
        self.event_file = event_file

    def get_dashboard_summary(self):
        if not self.event_file.exists():
            return {"error": "Event file not found"}

        events = []
        try:
            with open(self.event_file, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            events.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except Exception:
            return {"error": "Could not read event file"}

        if not events:
            return {"total_events": 0, "status": "no events"}

        event_types = Counter(e.get("event_type", "unknown") for e in events)
        severities = Counter(e.get("severity", "unknown") for e in events)

        latest_event = events[-1]

        # Filter metadata for safety - only expose non-sensitive fields
        safe_summaries = []
        for e in events[-10:]:
            summary = {
                "timestamp": e.get("timestamp"),
                "type": e.get("event_type"),
                "phase": e.get("phase")
            }
            safe_summaries.append(summary)

        summary = {
            "total_events": len(events),
            "latest_timestamp": latest_event.get("timestamp"),
            "event_types": dict(event_types),
            "severities": dict(severities),
            "latest_phase": latest_event.get("phase"),
            "latest_adjudication": latest_event.get("adjudication_decision"),
            "human_required": any(e.get("human_required", False) for e in events),
            "last_10_summaries": safe_summaries
        }
        return summary

    def generate_html(self, summary):
        if "error" in summary:
            return f"<html><body><h1>Error: {html.escape(summary['error'])}</h1></body></html>"

        # Start HTML
        html_content = []
        html_content.append("<!DOCTYPE html>")
        html_content.append("<html lang='en'>")
        html_content.append("<head>")
        html_content.append("    <meta charset='UTF-8'>")
        html_content.append("    <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        html_content.append("    <title>Hermes Harness Dashboard</title>")
        html_content.append("    <style>")
        html_content.append("        body { font-family: Arial, sans-serif; margin: 20px; }")
        html_content.append("        h1 { color: #2c3e50; }")
        html_content.append("        .section { margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }")
        html_content.append("        .section h2 { color: #3498db; margin-top: 0; }")
        html_content.append("        .data { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; }")
        html_content.append("        .data-item { background: #f8f9fa; padding: 10px; border-radius: 3px; }")
        html_content.append("        .label { font-weight: bold; color: #555; }")
        html_content.append("        .value { margin-top: 5px; }")
        html_content.append("        table { width: 100%; border-collapse: collapse; }")
        html_content.append("        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }")
        html_content.append("        th { background-color: #f2f2f2; }")
        html_content.append("        tr:nth-child(even) { background-color: #f9f9f9; }")
        html_content.append("    </style>")
        html_content.append("</head>")
        html_content.append("<body>")
        html_content.append("    <h1>Hermes Harndashboard</h1>")

        # Current Harness Status
        html_content.append("    <div class='section'>")
        html_content.append("        <h2>Current Harness Status</h2>")
        html_content.append("        <div class='data'>")
        html_content.append(f"            <div class='data-item'><div class='label'>Total Events</div><div class='value'>{html.escape(str(summary['total_events']))}</div></div>")
        html_content.append(f"            <div class='data-item'><div class='label'>Latest Timestamp</div><div class='value'>{html.escape(str(summary.get('latest_timestamp', 'N/A')))}</div></div>")
        html_content.append(f"            <div class='data-item'><div class='label'>Latest Phase</div><div class='value'>{html.escape(str(summary.get('latest_phase', 'N/A')))}</div></div>")
        html_content.append(f"            <div class='data-item'><div class='label'>Adjudication Decision</div><div class='value'>{html.escape(str(summary.get('latest_adjudication', 'N/A')))}</div></div>")
        html_content.append(f"            <div class='data-item'><div class='label'>Human Required</div><div class='value'>{html.escape(str(summary.get('human_required', False)))}</div></div>")
        html_content.append("        </div>")
        html_content.append("    </div>")

        # Event Counts by Type
        html_content.append("    <div class='section'>")
        html_content.append("        <h2>Event Counts by Type</h2>")
        html_content.append("        <div class='data'>")
        for event_type, count in summary.get('event_types', {}).items():
            html_content.append(f"            <div class='data-item'><div class='label'>{html.escape(event_type)}</div><div class='value'>{html.escape(str(count))}</div></div>")
        html_content.append("        </div>")
        html_content.append("    </div>")

        # Severity Counts
        html_content.append("    <div class='section'>")
        html_content.append("        <h2>Severity Counts</h2>")
        html_content.append("        <div class='data'>")
        for severity, count in summary.get('severities', {}).items():
            html_content.append(f"            <div class='data-item'><div class='label'>{html.escape(severity)}</div><div class='value'>{html.escape(str(count))}</div></div>")
        html_content.append("        </div>")
        html_content.append("    </div>")

        # Last 10 Events
        html_content.append("    <div class='section'>")
        html_content.append("        <h2>Last 10 Events</h2>")
        html_content.append("        <table>")
        html_content.append("            <thead>")
        html_content.append("                <tr>")
        html_content.append("                    <th>Timestamp</th>")
        html_content.append("                    <th>Type</th>")
        html_content.append("                    <th>Phase</th>")
        html_content.append("                </tr>")
        html_content.append("            </thead>")
        html_content.append("            <tbody>")
        for event in summary.get('last_10_summaries', []):
            html_content.append("                <tr>")
            html_content.append(f"                    <td>{html.escape(str(event.get('timestamp', '')))}</td>")
            html_content.append(f"                    <td>{html.escape(str(event.get('type', '')))}</td>")
            html_content.append(f"                    <td>{html.escape(str(event.get('phase', '')))}</td>")
            html_content.append("                </tr>")
        html_content.append("            </tbody>")
        html_content.append("        </table>")
        html_content.append("    </div>")

        # Git commit (optional)
        try:
            import subprocess
            result = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, cwd=self.event_file.parent.parent)
            git_commit = result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            git_commit = "unknown"

        html_content.append("    <div class='section'>")
        html_content.append("        <h2>Repository Info</h2>")
        html_content.append("        <div class='data'>")
        html_content.append(f"            <div class='data-item'><div class='label'>Git Commit</div><div class='value'>{html.escape(git_commit)}</div></div>")
        html_content.append("        </div>")
        html_content.append("    </div>")

        html_content.append("</body>")
        html_content.append("</html>")

        return "\n".join(html_content)

def main():
    event_file = Path("events/harness_events.jsonl")
    generator = DashboardGenerator(event_file)
    summary = generator.get_dashboard_summary()
    html_output = generator.generate_html(summary)

    output_dir = Path("dashboard")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "report.html"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_output)

    print(f"Dashboard generated at {output_file}")

if __name__ == "__main__":
    main()