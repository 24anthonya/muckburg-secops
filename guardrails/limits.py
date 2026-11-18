import psutil

MAX_LOCAL_RAM_PERCENT = 75.0
MAX_AGENT_STEPS = 10

def check_local_resources() -> dict:
    mem = psutil.virtual_memory()
    safe_to_run = mem.percent < MAX_LOCAL_RAM_PERCENT

    return {
        "safe": safe_to_run,
        "ram_used_percent": mem.percent,
        "available_gb": round(mem.available / (1024 ** 3), 2)
    }

def enforce_step_limit(current_step: int):
    if current_step > MAX_AGENT_STEPS:
        raise RuntimeError(
            f"Guardrail triggered: Exceeded max {MAX_AGENT_STEPS} steps."
        )
