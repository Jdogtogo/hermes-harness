ACTION GATE V0.2 IMPLEMENTATION PLAN

1. Files proposed for modification:
   - /home/jfroh/hermes/harness/action_gate_v0/action_gate.py
   - /home/jfroh/hermes/harness/action_gate_v0/run_tests.py (if needed to adjust test running, but likely not)

2. Files proposed for creation:
   - /home/jfroh/hermes/harness/action_gate_v0/schemas/preflight_manifest.json
   - /home/jfroh/hermes/harness/action_gate_v0/schemas/proposed_action.json
   - /home/jfroh/hermes/harness/action_gate_v0/schemas/loop_state.json
   - /home/jfroh/hermes/harness/action_gate_v0/schemas/gate_decision.json
   - 12 new test cases: tc_27.json through tc_38.json in /home/jfroh/hermes/harness/action_gate_v0/test_cases/

3. Files explicitly out of scope:
   - Any file outside /home/jfroh/hermes/harness/action_gate_v0/
   - Specifically: Hermes runtime, secrets, config, cron, Telegram, email, memory, financial/client-sensitive workflows.

4. Exact test cases to add:
   27. Missing risk_class → deny
   28. Unknown risk_class → deny
   29. Unknown action_type → deny
   30. Boolean provided as string → deny
   31. allowed_write_paths provided as string instead of list → deny
   32. Missing allowed_read_roots on read_file → deny
   33. Empty allowed_write_paths on write_file → deny
   34. Unknown mode → deny
   35. Missing loop_state → deny or lock_task
   36. Negative max_verification_fix_cycles → deny
   37. Missing action_id → deny
   38. Malformed path value, non-string path → deny

5. Verification commands:
   - cd /home/jfroh/hermes/harness/action_gate_v0
   - python3 run_tests.py

6. Rollback plan:
   - Backup the current state of the action_gate_v0 directory by copying it to a timestamped backup.
   - Alternatively, use git stash if the directory is under version control (it appears not to be, but we can check).
   - We will create a backup directory: /home/jfroh/hermes/harness/action_gate_v0_backup_$(date +%Y%m%d_%H%M%S)
   - Then copy the entire action_gate_v0 directory to that backup.
   - If we need to rollback, we can restore from the backup.

Note: We will first check if jsonschema is available. If not, we may need to install it via pip, but note the environment constraints.
However, the task does not prohibit installing packages in the isolated evaluator context. We will check and install if necessary.

Let's proceed.