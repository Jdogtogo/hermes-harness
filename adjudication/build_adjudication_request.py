import json
import argparse

def build_request(phase, report_path, commit, summary):
    request = {
        "phase": phase,
        "report_path": report_path,
        "commit": commit,
        "verification_summary": summary
    }
    with open("/home/jfroh/hermes/harness/adjudication/current_request.json", "w") as f:
        json.dump(request, f, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--summary", required=True)
    args = parser.parse_args()
    build_request(args.phase, args.report, args.commit, args.summary)
