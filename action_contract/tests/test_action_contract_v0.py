import unittest
import yaml
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from validator import ActionContractValidator

class TestActionContractV0(unittest.TestCase):
    def setUp(self):
        self.validator = ActionContractValidator()

    def test_valid_dry_run(self):
        with open('/home/jfroh/hermes/harness/action_contract/action.example.valid.yaml') as f:
            data = yaml.safe_load(f)
        result = self.validator.validate(data)
        self.assertEqual(result, 'ACTION_CONTRACT_VALID')

    def test_missing_workstream_scope(self):
        with open('/home/jfroh/hermes/harness/action_contract/action.example.missing_scope.yaml') as f:
            data = yaml.safe_load(f)
        result = self.validator.validate(data)
        self.assertEqual(result, 'ACTION_CONTRACT_ESCALATE')

    def test_invalid_enum(self):
        # create a copy of valid but change category to invalid
        with open('/home/jfroh/hermes/harness/action_contract/action.example.valid.yaml') as f:
            data = yaml.safe_load(f)
        data['workstream']['category'] = 'invalid'
        result = self.validator.validate(data)
        self.assertEqual(result, 'ACTION_CONTRACT_ESCALATE')

    def test_git_push_command(self):
        with open('/home/jfroh/hermes/harness/action_contract/action.example.forbidden_git_push.yaml') as f:
            data = yaml.safe_load(f)
        result = self.validator.validate(data)
        self.assertEqual(result, 'ACTION_CONTRACT_INVALID')

    def test_git_allow_push_true(self):
        with open('/home/jfroh/hermes/harness/action_contract/action.example.valid.yaml') as f:
            data = yaml.safe_load(f)
        data['git']['allow_push'] = True
        result = self.validator.validate(data)
        self.assertEqual(result, 'ACTION_CONTRACT_INVALID')

    def test_memory_allow_write_true(self):
        with open('/home/jfroh/hermes/harness/action_contract/action.example.memory_write.yaml') as f:
            data = yaml.safe_load(f)
        result = self.validator.validate(data)
        self.assertEqual(result, 'ACTION_CONTRACT_INVALID')

    def test_external_services_enabled_non_empty(self):
        with open('/home/jfroh/hermes/harness/action_contract/action.example.valid.yaml') as f:
            data = yaml.safe_load(f)
        data['external_services']['enabled'] = ['http']
        result = self.validator.validate(data)
        self.assertEqual(result, 'ACTION_CONTRACT_INVALID')

    def test_files_delete_non_empty(self):
        with open('/home/jfroh/hermes/harness/action_contract/action.example.valid.yaml') as f:
            data = yaml.safe_load(f)
        data['files']['delete'] = ['/tmp/test']
        result = self.validator.validate(data)
        self.assertEqual(result, 'ACTION_CONTRACT_INVALID')

    def test_missing_acceptance_criteria(self):
        with open('/home/jfroh/hermes/harness/action_contract/action.example.valid.yaml') as f:
            data = yaml.safe_load(f)
        data['acceptance_criteria'] = []
        result = self.validator.validate(data)
        self.assertEqual(result, 'ACTION_CONTRACT_ESCALATE')

    def test_missing_rollback_plan(self):
        with open('/home/jfroh/hermes/harness/action_contract/action.example.valid.yaml') as f:
            data = yaml.safe_load(f)
        data['rollback_plan'] = {}
        result = self.validator.validate(data)
        self.assertEqual(result, 'ACTION_CONTRACT_ESCALATE')

if __name__ == '__main__':
    unittest.main()