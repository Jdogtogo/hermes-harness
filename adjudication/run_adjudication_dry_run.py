import json
import argparse
from adjudication.adjudicator_client import adjudicate
from adjudication.build_adjudication_request import build_request

def run_dry_run():
    print("Running live-gated adjudication smoke test...")
    build_request(
        "guardrail-baseline",
        "/home/jfroh/hermes/harness/HERMES_GUARDRAIL_BASELINE_RESTORE_REPORT.md",
        "c602627",
        "Clean guardrail baseline restored. 44/44 tests passed."
    )
    
    # Simulate --live call (this calls the 'live' logic branch)
    # The current client will return the same mocked data but hit the 'live_mode' branch.
    response = adjudicate(
        "/home/jfroh/hermes/harness/adjudication/current_request.json",
        "/home/jfroh/hermes/harness/adjudication/live_extracted_response.json",
        live_mode=True
    )
    
    print("Decision:", response.decision)
    print("Should continue:", response.should_continue)
    print("Next action:", response.required_next_action)
    print("Instruction:", response.next_instruction_for_hermes)
    print("MANUAL GATE: no continuation performed")

if __name__ == "__main__":
    run_dry_run()
