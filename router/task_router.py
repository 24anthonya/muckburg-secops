import urllib.request
import json
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from guardrails.limits import check_local_resources

LOCAL_MODEL = "qwen2.5-coder:3b"

LOCAL_OLLAMA_URL = "http://localhost:11434/api/generate"
WINDOWS_VM_OLLAMA_URL = "http://localhost:11434/api/generate"


def route_task(prompt: str, complexity: str = "low") -> str:
    resources = check_local_resources()

    print(
        f"[Status] Local RAM: "
        f"{resources['ram_used_percent']}% "
        f"({resources['available_gb']} GB free)"
    )

    if complexity == "low" and resources["safe"]:
        print(
            f"[Router] Executing locally via Ollama API "
            f"({LOCAL_MODEL})..."
        )
        return call_ollama_api(LOCAL_OLLAMA_URL, prompt)

    print("[Router] Offloading task to Windows Server VM...")
    return call_ollama_api(WINDOWS_VM_OLLAMA_URL, prompt)


def call_ollama_api(endpoint_url: str, prompt: str) -> str:
    payload = json.dumps(
        {
            "model": LOCAL_MODEL,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "2m",
            "options": {
                "num_predict": 300,
                "temperature": 0.2,
                "num_ctx": 2048,
                "num_thread": 4
            }
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        endpoint_url,
        data=payload,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )

            return result.get(
                "response",
                ""
            ).strip()

    except Exception as e:
        return f"[Ollama Error] {e}"


if __name__ == "__main__":
    print(
        route_task(
            "Give me 1 quick HTTP security header tip.",
            complexity="low"
        )
    )
    