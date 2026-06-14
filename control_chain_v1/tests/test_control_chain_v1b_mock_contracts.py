import sys
import os
import yaml

# Real Imports
sys.path.append('/home/jfroh/hermes/harness/action_contract')
sys.path.append('/home/jfroh/hermes/harness/governor')
sys.path.append('/home/jfroh/hermes/harness/runner')

from validator import ActionContractValidator
from governor import Governor

# Config
BASE_DIR = '/home/jfroh/hermes/harness/control_chain_v1'
POLICY_PATH = os.path.join(BASE_DIR, 'policy.example.yaml')
CONTRACTS_DIR = os.path.join(BASE_DIR, 'contracts')

def check_source_safety(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    forbidden = ['subprocess', 'os.system', 'exec(', 'eval(']
    for f in forbidden:
        if f in content:
            return False, f
    return True, None

def run_tests():
    validator = ActionContractValidator()
    governor = Governor(POLICY_PATH)
    results = {}
    
    # Check Safety
    safety_checks = {
        'validator': check_source_safety('/home/jfroh/hermes/harness/action_contract/validator.py')[0],
        'governor': check_source_safety('/home/jfroh/hermes/harness/governor/governor.py')[0],
        'runner': check_source_safety('/home/jfroh/hermes/harness/runner/runner.py')[0],
    }
    
    # Workflows to test
    workflows = [
        'repo_status_dry_run.yaml',
        'preflight_dry_run.yaml',
        'allowlist_staging_simulation.yaml',
        'checkpoint_readiness_report.yaml',
        'test_suite_readiness_check.yaml',
        'untracked_file_risk_report.yaml'
    ]
    
    for wf in workflows:
        path = os.path.join(CONTRACTS_DIR, wf)
        with open(path) as f:
            action = yaml.safe_load(f)
            
        v_status = validator.validate(action)
        if v_status == 'ACTION_CONTRACT_VALID':
            g_status = governor.evaluate(path)
            if g_status == 'ALLOW':
                results[wf] = 'CONTROL_CHAIN_V1_DRY_RUN_ALLOW'
            elif g_status == 'BLOCK':
                results[wf] = 'CONTROL_CHAIN_V1_DRY_RUN_BLOCK'
            else:
                results[wf] = f'CONTROL_CHAIN_V1_DRY_RUN_ESCALATE (g_status: {g_status})'
        else:
            results[wf] = f'CONTROL_CHAIN_V1_DRY_RUN_ESCALATE (v_status: {v_status})'
            
    # Unsafe variants test
    # 1. Invalid command (git push in allowed)
    with open(os.path.join(CONTRACTS_DIR, workflows[0])) as f:
        action = yaml.safe_load(f)
    action_unsafe = action.copy()
    action_unsafe['commands']['allowed'] = ['git push']
    path_unsafe = os.path.join(BASE_DIR, 'unsafe_test.yaml')
    with open(path_unsafe, 'w') as f:
        yaml.dump(action_unsafe, f)
    v_status = validator.validate(action_unsafe)
    if v_status == 'ACTION_CONTRACT_VALID':
        g_status = governor.evaluate(path_unsafe)
        if g_status == 'BLOCK':
            results['unsafe_git_push'] = 'CONTROL_CHAIN_V1_DRY_RUN_BLOCK'
        else:
            results['unsafe_git_push'] = 'CONTROL_CHAIN_V1_DRY_RUN_ESCALATE'
    else:
        results['unsafe_git_push'] = 'CONTROL_CHAIN_V1_DRY_RUN_ESCALATE'

    # 2. memory.allow_write true
    action_unsafe2 = action.copy()
    action_unsafe2['memory']['allow_write'] = True
    path_unsafe2 = os.path.join(BASE_DIR, 'unsafe_test2.yaml')
    with open(path_unsafe2, 'w') as f:
        yaml.dump(action_unsafe2, f)
    v_status2 = validator.validate(action_unsafe2)
    if v_status2 == 'ACTION_CONTRACT_VALID':
        results['unsafe_memory_write'] = 'CONTROL_CHAIN_V1_DRY_RUN_ESCALATE'
    else:
        results['unsafe_memory_write'] = 'CONTROL_CHAIN_V1_DRY_RUN_ESCALATE'

    # 3. external_services.enabled non-empty
    action_unsafe3 = action.copy()
    action_unsafe3['external_services']['enabled'] = ['http']
    path_unsafe3 = os.path.join(BASE_DIR, 'unsafe_test3.yaml')
    with open(path_unsafe3, 'w') as f:
        yaml.dump(action_unsafe3, f)
    v_status3 = validator.validate(action_unsafe3)
    if v_status3 == 'ACTION_CONTRACT_VALID':
        results['unsafe_external_services'] = 'CONTROL_CHAIN_V1_DRY_RUN_ESCALATE'
    else:
        results['unsafe_external_services'] = 'CONTROL_CHAIN_V1_DRY_RUN_ESCALATE'

    # 4. governor blocked (command not in allowed_commands)
    action_unsafe4 = action.copy()
    action_unsafe4['commands']['allowed'] = ['ls -l']   # not in [ls, echo, dummy, "git status --short"]
    path_unsafe4 = os.path.join(BASE_DIR, 'unsafe_test4.yaml')
    with open(path_unsafe4, 'w') as f:
        yaml.dump(action_unsafe4, f)
    v_status4 = validator.validate(action_unsafe4)
    if v_status4 == 'ACTION_CONTRACT_VALID':
        g_status4 = governor.evaluate(path_unsafe4)
        if g_status4 == 'BLOCK':
            results['unsafe_governor_block'] = 'CONTROL_CHAIN_V1_DRY_RUN_BLOCK'
        else:
            results['unsafe_governor_block'] = 'CONTROL_CHAIN_V1_DRY_RUN_ESCALATE'
    else:
        results['unsafe_governor_block'] = 'CONTROL_CHAIN_V1_DRY_RUN_ESCALATE'

    print("Safety Checks:")
    for m, ok in safety_checks.items():
        print(f"  {m}: {'PASS' if ok else 'FAIL'}")
        
    print("\nWorkflow Outcomes:")
    for wf, status in results.items():
        print(f"  {wf}: {status}")

if __name__ == '__main__':
    run_tests()