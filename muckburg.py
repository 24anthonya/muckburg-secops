import argparse
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from router.task_router import route_task
from workflows.header_audit import audit_url_headers
from workflows.source_review import review_source_file

def main():
    parser = argparse.ArgumentParser(description="MuckBurg SecOps Hybrid AI CLI")
    parser.add_argument("prompt", nargs="?", help="Direct SecOps prompt to analyze")
    parser.add_argument("--audit", help="Run a live HTTP security header audit on a URL")
    parser.add_argument("--review", help="Run a security review on a source file")
    parser.add_argument("--heavy", action="store_true", help="Force offload to Windows Server VM")
    args = parser.parse_args()

    complexity = "high" if args.heavy else "low"

    if args.audit:
        print("\n--- Audit Report ---\n", audit_url_headers(args.audit, complexity=complexity))
    elif args.review:
        print("\n--- Source Review ---\n", review_source_file(args.review, complexity=complexity))
    elif args.prompt:
        print("\n--- Output ---\n", route_task(args.prompt, complexity=complexity))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
