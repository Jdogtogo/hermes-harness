import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from governor import Governor

def test_cases():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    governor_dir = os.path.dirname(base_dir)
    policy_path = os.path.join(governor_dir, "policy.example.yaml")
    g = Governor(policy_path)
    
    # 1. ALLOW test
    print(f"ALLOW test: {g.evaluate(os.path.join(governor_dir, 'action.example.allow.yaml'))}")
    
    # 2. BLOCK test (git push)
    print(f"BLOCK test: {g.evaluate(os.path.join(governor_dir, 'action.example.block.yaml'))}")
    
    # 3. ESCALATE test (mismatch)
    print(f"ESCALATE test: {g.evaluate(os.path.join(governor_dir, 'action.example.escalate.yaml'))}")

if __name__ == "__main__":
    test_cases()
