import yaml, json, sys
# Extract values
try:
    with open(sys.argv[1]) as f:
        config = yaml.safe_load(f)
        agent = config.get('agent', {})
        gateway = config.get('gateway', {})
        print(json.dumps({
            'environment_hint': agent.get('environment_hint', ''),
            'environment_probe': agent.get('environment_probe', False),
            'task_completion_guidance': agent.get('task_completion_guidance', False),
            'gateway_strict': gateway.get('strict', False)
        }))
except Exception as e:
    print(json.dumps({'error': str(e)}))
