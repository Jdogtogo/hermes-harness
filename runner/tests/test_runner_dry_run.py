import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from runner import Runner

def test_runner():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    runner_dir = os.path.dirname(base_dir)
    manifest_path = os.path.join(runner_dir, "manifest.example.yaml")
    runner = Runner(manifest_path)
    
    # 1. Allowed
    runner.run("ls", "/tmp/runner-test/file.txt")
    
    # 2. Forbidden command
    runner.run("rm", "/tmp/runner-test/file.txt")
    
    # 3. Git add blocked
    runner.run("git add .", "/tmp/runner-test/file.txt")
    
    # 4. Secret file
    runner.run("cat", "/tmp/runner-test/.env")
    
    # 5. Path escape
    runner.run("ls", "/tmp/runner-test/../../etc/passwd")

if __name__ == "__main__":
    test_runner()