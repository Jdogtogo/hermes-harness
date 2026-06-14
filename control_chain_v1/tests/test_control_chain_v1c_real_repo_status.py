import sys
import os
import yaml
import subprocess
import unittest
import inspect
sys.path.insert(0, '/home/jfroh/hermes/harness')

from action_contract.validator import ActionContractValidator
from governor.governor import Governor
from runner.runner import Runner

class TestControlChainV1C(unittest.TestCase):
    def setUp(self):
        self.contract_path = "/home/jfroh/hermes/harness/control_chain_v1/contracts/repo_status_real_read_only.yaml"
        self.policy_path = "/home/jfroh/hermes/harness/control_chain_v1/policies/repo_status_real_read_only_policy.yaml"
        self.manifest_path = "/home/jfroh/hermes/harness/runner/manifest.example.yaml"
        self.validator = ActionContractValidator()
        self.governor = Governor(self.policy_path)
        self.runner = Runner(self.manifest_path)
        with open(self.contract_path, 'r') as f:
            self.contract = yaml.safe_load(f)

    def test_validation_passes(self):
        v_result = self.validator.validate(self.contract)
        self.assertEqual(v_result, "ACTION_CONTRACT_VALID")

    def test_governor_allows(self):
        v_result = self.validator.validate(self.contract)
        self.assertEqual(v_result, "ACTION_CONTRACT_VALID")
        g_result = self.governor.evaluate(self.contract_path)
        self.assertEqual(g_result, "ALLOW")

    def test_runner_executes_and_passes(self):
        v_result = self.validator.validate(self.contract)
        self.assertEqual(v_result, "ACTION_CONTRACT_VALID")
        g_result = self.governor.evaluate(self.contract_path)
        self.assertEqual(g_result, "ALLOW")
        res = self.runner.run_v1c_repo_status("/home/jfroh/hermes/harness")
        self.assertEqual(res["status"], "CONTROL_CHAIN_V1C_REPO_STATUS_PASS")
        self.assertEqual(res["command"], "git status --short")
        self.assertEqual(res["working_directory"], "/home/jfroh/hermes/harness")
        self.assertEqual(res["returncode"], 0)

    def test_blocked_git_status_without_short(self):
        blocked_contract = self.contract.copy()
        blocked_contract["commands"]["allowed"] = ["git status"]
        with open("/tmp/test_blocked.yaml", 'w') as f:
            yaml.dump(blocked_contract, f)
        v_result = self.validator.validate(blocked_contract)
        self.assertEqual(v_result, "ACTION_CONTRACT_VALID")
        g_result = self.governor.evaluate("/tmp/test_blocked.yaml")
        self.assertEqual(g_result, "BLOCK")
        os.remove("/tmp/test_blocked.yaml")

    def test_blocked_git_add(self):
        blocked_contract = self.contract.copy()
        blocked_contract["commands"]["allowed"] = ["git add"]
        with open("/tmp/test_blocked.yaml", 'w') as f:
            yaml.dump(blocked_contract, f)
        v_result = self.validator.validate(blocked_contract)
        # Should be blocked either by validator or governor
        if v_result == "ACTION_CONTRACT_VALID":
            g_result = self.governor.evaluate("/tmp/test_blocked.yaml")
            self.assertEqual(g_result, "BLOCK")
        else:
            self.assertEqual(v_result, "ACTION_CONTRACT_INVALID")
        os.remove("/tmp/test_blocked.yaml")

    def test_blocked_git_commit(self):
        blocked_contract = self.contract.copy()
        blocked_contract["commands"]["allowed"] = ["git commit"]
        with open("/tmp/test_blocked.yaml", 'w') as f:
            yaml.dump(blocked_contract, f)
        v_result = self.validator.validate(blocked_contract)
        if v_result == "ACTION_CONTRACT_VALID":
            g_result = self.governor.evaluate("/tmp/test_blocked.yaml")
            self.assertEqual(g_result, "BLOCK")
        else:
            self.assertEqual(v_result, "ACTION_CONTRACT_INVALID")
        os.remove("/tmp/test_blocked.yaml")

    def test_blocked_git_push(self):
        blocked_contract = self.contract.copy()
        blocked_contract["commands"]["allowed"] = ["git push"]
        with open("/tmp/test_blocked.yaml", 'w') as f:
            yaml.dump(blocked_contract, f)
        v_result = self.validator.validate(blocked_contract)
        self.assertEqual(v_result, "ACTION_CONTRACT_INVALID")
        os.remove("/tmp/test_blocked.yaml")

    def test_blocked_command_with_env(self):
        blocked_contract = self.contract.copy()
        blocked_contract["commands"]["allowed"] = ["git", ".env"]
        with open("/tmp/test_blocked.yaml", 'w') as f:
            yaml.dump(blocked_contract, f)
        v_result = self.validator.validate(blocked_contract)
        self.assertNotEqual(v_result, "ACTION_CONTRACT_VALID")
        os.remove("/tmp/test_blocked.yaml")

    def test_blocked_wrong_working_directory(self):
        v_result = self.validator.validate(self.contract)
        self.assertEqual(v_result, "ACTION_CONTRACT_VALID")
        g_result = self.governor.evaluate(self.contract_path)
        self.assertEqual(g_result, "ALLOW")
        res = self.runner.run_v1c_repo_status("/home/jfroh")
        self.assertEqual(res["status"], "CONTROL_CHAIN_V1C_REPO_STATUS_BLOCKED")

    def test_malformed_contract_escalated(self):
        malformed = self.contract.copy()
        del malformed["action_id"]
        with open("/tmp/test_malformed.yaml", 'w') as f:
            yaml.dump(malformed, f)
        v_result = self.validator.validate(malformed)
        self.assertEqual(v_result, "ACTION_CONTRACT_ESCALATE")
        os.remove("/tmp/test_malformed.yaml")

    def test_runner_does_not_accept_command_parameter(self):
        sig = inspect.signature(self.runner.run_v1c_repo_status)
        self.assertListEqual(list(sig.parameters.keys()), ["working_directory"])

    def test_runner_uses_shell_false(self):
        with open("/home/jfroh/hermes/harness/runner/runner.py", 'r') as f:
            content = f.read()
        self.assertIn("shell=False", content)
        self.assertNotIn("shell=True", content)

if __name__ == "__main__":
    unittest.main()
