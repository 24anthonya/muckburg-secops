import urllib.request
import urllib.error
import ssl
import sys
import os

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from router.task_router import route_task


def audit_url_headers(
    url: str,
    complexity: str = "low"
) -> str:

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    print(f"[Scanner] Fetching live headers from {url}...")

    req = urllib.request.Request(
        url,
        method="HEAD",
        headers={
            "User-Agent": "MuckBurg-SecOps/1.0"
        }
    )

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(
            req,
            timeout=15,
            context=ctx
        ) as resp:

            headers_text = "\n".join(
                f"{k}: {v}"
                for k, v in resp.headers.items()
            )

    except urllib.error.HTTPError as e:

        headers_text = "\n".join(
            f"{k}: {v}"
            for k, v in e.headers.items()
        )

    except Exception as e:
        return (
            f"[Scanner Error] "
            f"Could not reach {url}: {e}"
        )

    prompt = (
        f"Analyze these HTTP response headers from "
        f"{url} for security misconfigurations, "
        f"missing security headers, or information "
        f"disclosure. Be concise and actionable:\n\n"
        f"{headers_text}"
    )

    return route_task(
        prompt,
        complexity=complexity
    )


if __name__ == "__main__":

    target = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "https://example.com"
    )

    print(
        "\n--- Audit Report ---\n",
        audit_url_headers(target)
    )
    