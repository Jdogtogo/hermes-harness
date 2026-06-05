import json
import sys
from pathlib import Path
from collections import Counter
from datetime import datetime

class EventConsumer:
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

def main():
    consumer = EventConsumer(Path("events/harness_events.jsonl"))
    summary = consumer.get_dashboard_summary()
    
    if "error" in summary:
        print(f"Error: {summary['error']}")
        return
        
    print("--- Dashboard Event Summary ---")
    print(f"Total Events: {summary['total_events']}")
    print(f"Latest Timestamp: {summary['latest_timestamp']}")
    print(f"Event Types: {summary['event_types']}")
    print(f"Severities: {summary['severities']}")
    print(f"Latest Phase: {summary['latest_phase']}")
    print(f"Adjudication Decision: {summary['latest_adjudication']}")
    print(f"Human Required: {summary['human_required']}")
    print("--- Last 10 Summaries ---")
    for s in summary['last_10_summaries']:
        print(s)

if __name__ == "__main__":
    main()
