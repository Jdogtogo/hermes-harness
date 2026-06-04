import json
import sys

def validate_adjudication_response(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"FAIL: Could not read or parse JSON file: {e}")
        return False

    required_keys = [
        "decision", "phase", "maturity_classification", "blocking_issues",
        "accepted_items", "required_next_action", "next_instruction_for_hermes", "should_continue"
    ]
    
    # Check keys
    for key in required_keys:
        if key not in data:
            print(f"FAIL: Missing required key: {key}")
            return False

    # Validate decision
    valid_decisions = ["approved", "rejected", "revise", "stop"]
    if data["decision"] not in valid_decisions:
        print(f"FAIL: Invalid decision value: {data['decision']}")
        return False

    # Validate should_continue
    if data["should_continue"] is True and data["decision"] != "approved":
        print("FAIL: should_continue is True but decision is not approved")
        return False

    print("PASS: Adjudication response is valid.")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 validate_adjudication_response.py <file_path>")
        sys.exit(1)
    
    if validate_adjudication_response(sys.argv[1]):
        sys.exit(0)
    else:
        sys.exit(1)
