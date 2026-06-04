"""
Hermes Multi-Agent Harness v1 — Smoke Test

End-to-end path through the harness with no LLM calls:
  1. Build a HarnessJob with all three role types.
  2. Route through Supervisor.
  3. Write to StateStore.
  4. Read back and verify.
  5. Print pass/fail summary.

Usage:
    /home/jfroh/hermes/harness_venv/bin/python /home/jfroh/hermes/harness/run_harness_smoke_test.py
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

# The harness is now in /home/jfroh/hermes/harness/, which is 
# in the current working directory, so it should be importable directly.

from harness.job_models  import HarnessJob, HarnessTask, JobStatus, RoleType
from harness.supervisor  import Supervisor
from harness.state_store import StateStore
from harness.validators  import validate_job

SMOKE_JOB_ID = "smoke-test-job-v1-001"
