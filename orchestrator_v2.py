import asyncio, json, subprocess, sys
from pydantic import BaseModel, Field, ValidationError

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

async def main():
    base_path = '/mnt/h/My Drive/Hermes_Workspace/Setup/config.yaml'
    core_path = '/home/jfroh/.hermes/profiles/workspace-core/config.yaml'

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
