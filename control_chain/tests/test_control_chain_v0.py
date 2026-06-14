import sys
import os
import yaml
import tempfile
import shutil

# Real Imports
sys.path.append('/home/jfroh/hermes/harness/action_contract')
sys.path.append('/home/jfroh/hermes/harness/governor')
sys.path.append('/home/jfroh/hermes/harness/runner')

from validator import ActionContractValidator
from governor import Governor
from runner import Runner

# Dummy data for governor/runner
POLICY_PATH = '/home/jfroh/hermes/harness/governor/policy.example.yaml'
MANIFEST_PATH = '/home/jfroh/hermes/harness/runner/manifest.example.yaml'

def check_source_safety(module_path):
    """Check that the module does not contain forbidden functions."""
    with open(module_path, 'r') as f:
        content = f.read()
    forbidden = ['subprocess', 'os.system', 'exec(', 'eval(']
    for f in forbidden:
        if f in content:
            return False, f
    return True, None

def run_integration():
    results = {}
    safety_checks = {}
    
    # Init components
    validator = ActionContractValidator()
    governor = Governor(POLICY_PATH)
    runner = Runner(MANIFEST_PATH)
    
    # Source safety check
    safety_checks['validator'], msg = check_source_safety('/home/jfroh/hermes/harness/action_contract/validator.py')
    safety_checks['governor'], msg = check_source_safety('/home/jfroh/hermes/harness/governor/governor.py')
    safety_checks['runner'], msg = check_source_safety('/home/jfroh/hermes/harness/runner/runner.py')
    
    # Create a temporary directory for test action files
    temp_dir = tempfile.mkdtemp(dir='/home/jfroh/hermes/harness/control_chain/tests')
    try:
        # 1. Valid Action Test
        with open('/home/jfroh/hermes/harness/action_contract/action.example.valid.yaml') as f:
            action = yaml.safe_load(f)
        
        v_status = validator.validate(action)
        if v_status == 'ACTION_CONTRACT_VALID':
            # Write action to temp file for governor
            action_file = os.path.join(temp_dir, 'valid_action.yaml')
            with open(action_file, 'w') as f:
                yaml.dump(action, f)
            g_status = governor.evaluate(action_file)
            if g_status == 'ALLOW':
                r_status = runner.run(action['commands']['allowed'][0], path="/tmp/test")
                results['valid_action'] = f"PASS (v:{v_status}, g:{g_status}, r:{r_status})"
            else:
                results['valid_action'] = f"FAIL (governor blocked: {g_status})"
        else:
            results['valid_action'] = f"FAIL (validator rejected: {v_status})"

        # 2. Invalid Action Test (Invalid enum)
        action_inv = action.copy()
        action_inv['workstream'] = {'name': 'test', 'category': 'invalid'}
        v_status_inv = validator.validate(action_inv)
        if v_status_inv == 'ACTION_CONTRACT_ESCALATE':
            results['invalid_action'] = "PASS (stopped before governor)"
        else:
            results['invalid_action'] = "FAIL (did not stop)"
            
        # 3. Escalated Action Test (Missing required field - remove workstream)
        action_esc = action.copy()
        del action_esc['workstream']
        v_status_esc = validator.validate(action_esc)
        if v_status_esc == 'ACTION_CONTRACT_ESCALATE':
            results['escalated_action'] = "PASS (stopped before governor)"
        else:
            results['escalated_action'] = "FAIL (did not stop)"
            
        # 4. Governor Blocked Test (Valid action but command not allowed)
        action_block = action.copy()
        # Change allowed command to something not in governor's allowed_commands and not matching forbidden patterns
        action_block['commands']['allowed'] = ['ls -l']  # not in [ls, echo, dummy] and not matching .env, etc.
        # Write action to temp file for governor
        action_file_block = os.path.join(temp_dir, 'blocked_action.yaml')
        with open(action_file_block, 'w') as f:
            yaml.dump(action_block, f)
        g_status_block = governor.evaluate(action_file_block)
        if g_status_block == 'BLOCK':
            results['governor_blocked'] = "PASS (stopped before runner)"
        else:
            results['governor_blocked'] = f"FAIL (expected BLOCK, got {g_status_block})"
            
        # 5. Governor Escalated Test (Valid action but workstream mismatch)
        action_esc_gov = action.copy()
        # Change workstream to not match policy (policy workstream is harness-test/runner)
        action_esc_gov['workstream'] = {'name': 'test', 'category': 'git'}
        # Write action to temp file for governor
        action_file_esc_gov = os.path.join(temp_dir, 'esc_gov_action.yaml')
        with open(action_file_esc_gov, 'w') as f:
            yaml.dump(action_esc_gov, f)
        g_status_esc_gov = governor.evaluate(action_file_esc_gov)
        if g_status_esc_gov == 'ESCALATE':
            results['governor_escalated'] = "PASS (stopped before runner)"
        else:
            results['governor_escalated'] = f"FAIL (expected ESCALATE, got {g_status_esc_gov})"
            
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir)
    
    return results, safety_checks

if __name__ == '__main__':
    res, safety = run_integration()
    print("Safety Checks:")
    for module, ok in safety.items():
        print(f"  {module}: {'PASS' if ok else 'FAIL'}")
    print("\nTest Results:")
    for k, v in res.items():
        print(f"{k}: {v}")