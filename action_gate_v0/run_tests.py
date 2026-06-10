import json
import os
from pathlib import Path
from action_gate import gate

def run_test(case_file):
    with open(case_file, 'r') as f:
        data = json.load(f)
    
    # Handle tc_14 symlink setup
    if data['case_id'] == 'tc_14':
        link = Path('/home/jfroh/hermes/harness/link_to_protected.txt')
        target = Path('/home/jfroh/.hermes/secrets/')
        if not link.exists():
            os.symlink(target, link)
            
    try:
        # Use .get to avoid KeyError for intentionally missing fields
        proposed_action = data.get('proposed_action', {})
        manifest = data.get('manifest', {})
        loop_state = data.get('loop_state', {})
        
        decision, reason = gate(proposed_action, manifest, loop_state)
        
        passed = decision == data['expected_decision']
    finally:
        # Cleanup tc_14 symlink
        if data['case_id'] == 'tc_14':
            link = Path('/home/jfroh/hermes/harness/link_to_protected.txt')
            if link.is_symlink():
                os.remove(link)
    
    return {
        "case": data['case_id'],
        "description": data['description'],
        "passed": passed,
        "decision": decision,
        "expected": data['expected_decision'],
        "reason": reason
    }

results = []
for f in sorted(os.listdir('test_cases')):
    if f.endswith('.json'):
        results.append(run_test(os.path.join('test_cases', f)))

with open('evidence_report.md', 'w') as f:
    f.write("# V0.2 ACTION GATE EVIDENCE REPORT\n\n")
    f.write(f"Results for {len(results)} test cases:\n\n")
    for r in results:
        f.write(f"- {r['case']}: {r['description']}\n")
        f.write(f"  Passed: {r['passed']}\n")
        f.write(f"  Decision: {r['decision']} (Expected: {r['expected']})\n")
        f.write(f"  Reason: {r['reason']}\n\n")

# Report failure if any test failed
failed = [r for r in results if not r['passed']]
if failed:
    print(f"FAILED {len(failed)} tests: {json.dumps(failed)}")
else:
    print(json.dumps(results))
