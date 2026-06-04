import json
from adjudication.adjudicator_client import adjudicate
from adjudication.build_adjudication_request import build_request

def run_dry_run():
    print("Running dry-run adjudication loop...")
    build_request(
        "guardrail-baseline",
        "/home/jfroh/hermes/harness/HERMES_GUARDRAIL_BASELINE_RESTORE_REPORT.md",
        "c602627",
        "Clean guardrail baseline restored. 44/44 tests passed."
    )
    
    response = adjudicate(
        "/home/jfroh/hermes/harness/adjudication/current_request.json",
        "/home/jfroh/hermes/harness/adjudication/current_response.json",
        mock_mode=True
    )
    
    print(f"Decision: {response.decision}")
    print(f"Should continue: {response.should_continue}")
    print(f"Next action: {response.required_next_action}")
    print(f"Instruction: {response.next_instruction_for_hermes}")

if __name__ == "__main__":
    run_dry_run()
