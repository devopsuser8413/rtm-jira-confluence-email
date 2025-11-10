\
import os
import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests

from utils import setup_logging, ensure_dir, read_env, get_env

log = logging.getLogger("jira")

def _auth(user: str, token: str):
    return (user, token)

def _allowed(name: str, name_contains: Optional[str], allowed_exts: Optional[List[str]]) -> bool:
    if name_contains and name_contains.lower() not in name.lower():
        return False
    if allowed_exts:
        ok = any(name.lower().endswith("." + ext.lower().lstrip(".")) for ext in allowed_exts)
        if not ok:
            return False
    return True

def fetch_from_issue(base: str, user: str, token: str, issue_key: str,
                     out_dir: str, name_contains: Optional[str], allowed_exts: Optional[List[str]]) -> List[str]:
    url = f"{base}/rest/api/3/issue/{issue_key}?fields=attachment"
    r = requests.get(url, auth=_auth(user, token))
    r.raise_for_status()
    data = r.json()
    attachments = (data.get("fields", {}) or {}).get("attachment", []) or []
    saved = []
    ensure_dir(out_dir)
    for a in attachments:
        name = a.get("filename")
        content = a.get("content")  # direct download URL
        if not name or not content:
            continue
        if not _allowed(name, name_contains, allowed_exts):
            continue
        log.info(f"Downloading: {name}")
        resp = requests.get(content, auth=_auth(user, token), stream=True)
        resp.raise_for_status()
        dest = Path(out_dir) / name
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        saved.append(dest.as_posix())
    return saved

def fetch_from_jql(base: str, user: str, token: str, jql: str,
                   out_dir: str, name_contains: Optional[str], allowed_exts: Optional[List[str]]) -> List[str]:
    # Search issues, then iterate
    url = f"{base}/rest/api/3/search"
    start_at = 0
    max_results = 50
    saved = []
    ensure_dir(out_dir)
    while True:
        payload = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results,
            "fields": ["attachment"]
        }
        r = requests.post(url, auth=_auth(user, token), json=payload)
        r.raise_for_status()
        data = r.json()
        issues = data.get("issues", [])
        if not issues:
            break
        for issue in issues:
            key = issue.get("key")
            fields = issue.get("fields", {}) or {}
            attachments = fields.get("attachment", []) or []
            for a in attachments:
                name = a.get("filename")
                content = a.get("content")
                if not name or not content:
                    continue
                if not _allowed(name, name_contains, allowed_exts):
                    continue
                log.info(f"[{key}] Downloading: {name}")
                resp = requests.get(content, auth=_auth(user, token), stream=True)
                resp.raise_for_status()
                dest = Path(out_dir) / name
                with open(dest, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                saved.append(dest.as_posix())
        start_at += max_results
        if start_at >= data.get("total", 0):
            break
    return saved

def main():
    setup_logging()
    read_env()
    base = get_env("JIRA_BASE", required=True).rstrip("/")
    user = get_env("JIRA_USER", required=True)
    token = get_env("JIRA_TOKEN", required=True)

    issue_key = os.getenv("JIRA_ISSUE_KEY", "").strip()
    jql = os.getenv("JIRA_JQL", "").strip()

    report_dir = os.getenv("REPORT_DIR", "report")
    name_contains = os.getenv("ATTACH_NAME_CONTAINS", "").strip() or None
    allowed_exts = [s.strip() for s in os.getenv("ATTACH_EXTS", "").split(",") if s.strip()] or None

    if not issue_key and not jql:
        raise RuntimeError("Provide JIRA_ISSUE_KEY or JIRA_JQL.")

    saved = []
    if issue_key:
        saved = fetch_from_issue(base, user, token, issue_key, report_dir, name_contains, allowed_exts)
    else:
        saved = fetch_from_jql(base, user, token, jql, report_dir, name_contains, allowed_exts)

    log.info(f"Saved files: {saved}")
    print(json.dumps({"saved": saved}, indent=2))

if __name__ == "__main__":
    main()
