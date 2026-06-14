import os
import yaml

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

    def run_v1c_repo_status(self, working_directory):
        if working_directory != "/home/jfroh/hermes/harness":
            return {"status": "CONTROL_CHAIN_V1C_REPO_STATUS_BLOCKED", "command": "git status --short"}
        
        import subprocess
        result = subprocess.run(
            ["git", "status", "--short"],
            shell=False,
            check=False,
            capture_output=True,
            text=True,
            cwd=working_directory
        )
        return {
            "status": "CONTROL_CHAIN_V1C_REPO_STATUS_PASS" if result.returncode == 0 else "CONTROL_CHAIN_V1C_REPO_STATUS_FAILED",
            "command": "git status --short",
            "working_directory": working_directory,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
