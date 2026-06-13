import asyncio, json, subprocess, sys, os, shutil
from pydantic import BaseModel, Field, ValidationError

# ── Path constants ──────────────────────────────────────────────────────────────
# Local WSL workspace is canonical. Google Drive is optional reference only.
LOCAL_WORKSPACE       = os.path.expanduser("~/.hermes/workspace")
LOCAL_SETUP_DIR       = os.path.join(LOCAL_WORKSPACE, "setup")
DRIVE_WORKSPACE       = "/mnt/h/My Drive/Hermes_Workspace"
DRIVE_SETUP_DIR       = os.path.join(DRIVE_WORKSPACE, "Setup")

LOCAL_CONFIG_SNAPSHOT = os.path.join(LOCAL_SETUP_DIR, "config_snapshot.yaml")
DRIVE_CONFIG_PATH     = os.path.join(DRIVE_SETUP_DIR, "config.yaml")

# Config Schema
class ConfigResult(BaseModel):
    environment_hint: str = Field(default='')
    environment_probe: bool = False
    task_completion_guidance: bool = False
    gateway_strict: bool = False

# Worker Task
async def run_worker(path):
    proc = await asyncio.create_subprocess_exec(
        'python3', '/tmp/harness/worker.py', path,
        stdout=subprocess.PIPE
    )
    stdout, _ = await proc.communicate()
    data = json.loads(stdout)
    return ConfigResult(**data)

# Orchestrator with Semaphore
MAX_CONCURRENT = 2
semaphore = asyncio.Semaphore(MAX_CONCURRENT)
MAX_RETRIES = 2

async def task_wrapper(path):
    for i in range(MAX_RETRIES + 1):
        async with semaphore:
            try:
                return await run_worker(path)
            except (ValidationError, Exception) as e:
                if i == MAX_RETRIES:
                    raise e
                await asyncio.sleep(0.1)


def refresh_config_snapshot():
    """Refresh local config snapshot from Drive if Drive is available.

    Returns the snapshot path to use as base_path, or None if no snapshot
    exists and Drive is also unavailable (drift check will be skipped).
    """
    os.makedirs(LOCAL_SETUP_DIR, exist_ok=True)

    if os.path.isfile(DRIVE_CONFIG_PATH):
        try:
            shutil.copyfile(DRIVE_CONFIG_PATH, LOCAL_CONFIG_SNAPSHOT)
            print("[orchestrator] Config snapshot refreshed from Drive", file=sys.stderr)
        except (OSError, shutil.Error) as e:
            print(f"[orchestrator] WARN: Could not refresh snapshot from Drive: {e}",
                  file=sys.stderr)
    else:
        print(f"[orchestrator] WARN: Drive config not available at {DRIVE_CONFIG_PATH} "
              f"— using cached snapshot if present", file=sys.stderr)

    if os.path.isfile(LOCAL_CONFIG_SNAPSHOT):
        return LOCAL_CONFIG_SNAPSHOT

    print("[orchestrator] WARN: No config snapshot available — skipping drift check",
          file=sys.stderr)
    return None


async def main():
    core_path = '/home/jfroh/.hermes/profiles/workspace-core/config.yaml'

    # Prefer local snapshot; refresh from Drive when available
    base_path = refresh_config_snapshot()

    if base_path is None:
        # No snapshot and no Drive — cannot perform drift check
        print(json.dumps({}))
        return

    results = await asyncio.gather(task_wrapper(base_path), task_wrapper(core_path))
    base_config, core_config = results

    # Compute drift
    patch = {}
    if base_config.environment_hint != core_config.environment_hint:
        patch['agent.environment_hint'] = base_config.environment_hint
    if base_config.environment_probe != core_config.environment_probe:
        patch['agent.environment_probe'] = base_config.environment_probe
    if base_config.task_completion_guidance != core_config.task_completion_guidance:
        patch['agent.task_completion_guidance'] = base_config.task_completion_guidance
    if base_config.gateway_strict != core_config.gateway_strict:
        patch['gateway.strict'] = base_config.gateway_strict

    print(json.dumps(patch, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
