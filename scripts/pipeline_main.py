\
import json
import os
import subprocess
import sys
from pathlib import Path

from utils import setup_logging, read_env, bump_version, get_env, ensure_dir

def run_step(name: str, args: list, cwd: str = None):
    print(f"\n=== {name} ===")
    print(" ".join(args))
    res = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    print(res.stdout)
    if res.returncode != 0:
        print(res.stderr, file=sys.stderr)
        raise SystemExit(f"{name} failed with exit code {res.returncode}")

def main():
    setup_logging()
    read_env()

    report_dir = os.getenv("REPORT_DIR", "report")
    version_file = os.getenv("VERSION_FILE", os.path.join(report_dir, "version.txt"))
    ensure_dir(report_dir)
    version = bump_version(version_file)
    print(f"Version bumped to: {version}")

    # Step 1: Jira → download attachments
    run_step("Fetch Jira Attachments", [sys.executable, "scripts/fetch_jira_attachments.py"])

    # Step 2: Confluence → publish page + attach
    # Capture the link and export to env for step 3
    p = subprocess.run([sys.executable, "scripts/confluence_publish.py"], capture_output=True, text=True)
    print(p.stdout)
    if p.returncode != 0:
        print(p.stderr, file=sys.stderr)
        raise SystemExit("Confluence publish failed")
    data = json.loads(p.stdout)
    link = data.get("link", "")
    os.environ["CONFLUENCE_PAGE_LINK"] = link
    print(f"Confluence page: {link}")

    # Step 3: Email → send attachments + link
    run_step("Send Email", [sys.executable, "scripts/send_email.py"])

if __name__ == "__main__":
    main()
