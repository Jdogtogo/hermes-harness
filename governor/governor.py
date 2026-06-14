import yaml
import re

class Governor:
    def __init__(self, policy_path):
        with open(policy_path, 'r') as f:
            self.policy = yaml.safe_load(f)

    def evaluate(self, action_path, evidence=None):
        with open(action_path, 'r') as f:
            action = yaml.safe_load(f)

        # 1. Workstream Check
        if action.get("workstream") != self.policy.get("workstream"):
            return "ESCALATE"

        # 2. Command Check
        cmds = action.get("commands", {}).get("allowed", [])
        for cmd in cmds:
            if cmd not in self.policy.get("allowed_commands", []):
                return "BLOCK"
            if any(re.search(pat, cmd) for pat in self.policy.get("forbidden_patterns", [])):
                return "BLOCK"

        # 3. Evidence Check
        if evidence is not None and not evidence.get("pass_fail", False):
            return "BLOCK"

        return "ALLOW"
