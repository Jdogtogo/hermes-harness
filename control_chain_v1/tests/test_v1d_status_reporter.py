import unittest
import sys
import os
sys.path.insert(0, '/home/jfroh/hermes/harness')
from control_chain_v1.reporters.status_reporter import StatusReporter

class TestStatusReporter(unittest.TestCase):
    def setUp(self):
        self.reporter = StatusReporter()

    def test_clean_stdout(self):
        result = {"status": "CONTROL_CHAIN_V1C_REPO_STATUS_PASS", "returncode": 0, "stdout": ""}
        report = self.reporter.report(result)
        self.assertFalse(report["repo_dirty"])
        self.assertEqual(report["recommendation"], "no_action")

    def test_untracked_archive(self):
        result = {"status": "CONTROL_CHAIN_V1C_REPO_STATUS_PASS", "returncode": 0, "stdout": "?? archive/data"}
        report = self.reporter.report(result)
        self.assertTrue(report["repo_dirty"])
        self.assertIn("archive/data", report["files_by_category"]["untracked"])

    def test_modified_file(self):
        result = {"status": "CONTROL_CHAIN_V1C_REPO_STATUS_PASS", "returncode": 0, "stdout": "M  file.txt"}
        report = self.reporter.report(result)
        self.assertIn("file.txt", report["files_by_category"]["modified"])

    def test_added_file(self):
        result = {"status": "CONTROL_CHAIN_V1C_REPO_STATUS_PASS", "returncode": 0, "stdout": "A  new.txt"}
        report = self.reporter.report(result)
        self.assertIn("new.txt", report["files_by_category"]["added"])

    def test_deleted_file(self):
        result = {"status": "CONTROL_CHAIN_V1C_REPO_STATUS_PASS", "returncode": 0, "stdout": "D  old.txt"}
        report = self.reporter.report(result)
        self.assertIn("old.txt", report["files_by_category"]["deleted"])

    def test_renamed_file(self):
        result = {"status": "CONTROL_CHAIN_V1C_REPO_STATUS_PASS", "returncode": 0, "stdout": "R  from.txt -> to.txt"}
        report = self.reporter.report(result)
        self.assertIn("from.txt -> to.txt", report["files_by_category"]["renamed"])

    def test_copied_file(self):
        result = {"status": "CONTROL_CHAIN_V1C_REPO_STATUS_PASS", "returncode": 0, "stdout": "C  source.txt -> copy.txt"}
        report = self.reporter.report(result)
        self.assertIn("source.txt -> copy.txt", report["files_by_category"]["copied"])

    def test_multiple_status_lines(self):
        stdout = "M  mod.txt\n?? untracked.txt"
        result = {"status": "CONTROL_CHAIN_V1C_REPO_STATUS_PASS", "returncode": 0, "stdout": stdout}
        report = self.reporter.report(result)
        self.assertEqual(len(report["files_by_category"]), 2)

    def test_unknown_status(self):
        result = {"status": "CONTROL_CHAIN_V1C_REPO_STATUS_PASS", "returncode": 0, "stdout": "XX mystery.txt"}
        report = self.reporter.report(result)
        self.assertIn("XX mystery.txt", report["files_by_category"]["unknown"])

    def test_missing_v1c_status(self):
        result = {"not_status": "none"}
        report = self.reporter.report(result)
        self.assertEqual(report["status"], "CONTROL_CHAIN_V1D_STATUS_REPORT_ESCALATED")

    def test_failed_v1c_status(self):
        result = {"status": "CONTROL_CHAIN_V1C_REPO_STATUS_FAILED", "returncode": 0, "stdout": ""}
        report = self.reporter.report(result)
        self.assertEqual(report["status"], "CONTROL_CHAIN_V1D_STATUS_REPORT_BLOCKED")

    def test_nonzero_returncode(self):
        result = {"status": "CONTROL_CHAIN_V1C_REPO_STATUS_PASS", "returncode": 1, "stdout": ""}
        report = self.reporter.report(result)
        self.assertEqual(report["status"], "CONTROL_CHAIN_V1D_STATUS_REPORT_BLOCKED")

    def test_raw_stdout_preserved_exactly(self):
        raw = "  M  file.txt\n??  other.txt\n  "
        result = {"status": "CONTROL_CHAIN_V1C_REPO_STATUS_PASS", "returncode": 0, "stdout": raw}
        report = self.reporter.report(result)
        self.assertEqual(report["raw_stdout"], raw)

    def test_no_subprocess_usage_in_reporter(self):
        with open("/home/jfroh/hermes/harness/control_chain_v1/reporters/status_reporter.py", "r") as f:
            content = f.read()
        self.assertNotIn("subprocess", content)

    def test_no_shell_true_in_reporter(self):
        with open("/home/jfroh/hermes/harness/control_chain_v1/reporters/status_reporter.py", "r") as f:
            content = f.read()
        self.assertNotIn("shell=True", content)

if __name__ == "__main__":
    unittest.main()
