import os
import yaml
from pathlib import Path

KILL_SWITCH = "/home/jfroh/.hermes/runtime/autonomy_runner.disabled"

class Runner:
    def __init__(self, manifest_path):
        with open(manifest_path, 'r') as f:
            self.manifest = yaml.safe_load(f)

    def is_blocked(self, cmd, path):
        if os.path.exists(KILL_SWITCH):
            return "AUTONOMY_RUNNER_BLOCKED"
        if cmd in self.manifest.get("forbidden_commands", []):
            return "AUTONOMY_RUNNER_BLOCKED"
        if "git add" in cmd or "git push" in cmd:
            return "AUTONOMY_RUNNER_BLOCKED"
        if any(f in path for f in self.manifest.get("forbidden_files", [])):
            return "AUTONOMY_RUNNER_BLOCKED"
        if ".." in path:
            return "AUTONOMY_RUNNER_BLOCKED"
        return "AUTONOMY_RUNNER_PASS"

    def run(self, cmd, path="/tmp/runner-test/file.txt"):
        status = self.is_blocked(cmd, path)
        print(f"[{status}] cmd={cmd}, path={path}")
        return status
