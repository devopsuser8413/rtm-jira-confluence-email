\
import os
import json
import logging
from typing import Optional, Tuple, Dict, Any, List

import requests

from utils import setup_logging, read_env, get_env

log = logging.getLogger("confluence")

def _auth(user: str, token: str):
    return (user, token)

def get_page_by_title(base: str, user: str, token: str, space: str, title: str) -> Optional[Dict[str, Any]]:
    url = f"{base}/rest/api/content"
    params = {
        "spaceKey": space,
        "title": title,
        "expand": "version,ancestors"
    }
    r = requests.get(url, params=params, auth=_auth(user, token))
    r.raise_for_status()
    results = (r.json().get("results", []) or [])
    return results[0] if results else None

def get_page_by_title_any_parent(base: str, user: str, token: str, title: str) -> Optional[Dict[str, Any]]:
    url = f"{base}/rest/api/content"
    params = {
        "title": title,
        "expand": "version,space,ancestors"
    }
    r = requests.get(url, params=params, auth=_auth(user, token))
    r.raise_for_status()
    results = (r.json().get("results", []) or [])
    return results[0] if results else None

def get_page_by_title_under_parent(base: str, user: str, token: str, space: str, parent_title: str, title: str) -> Optional[Dict[str, Any]]:
    # Find parent page
    parent = get_page_by_title(base, user, token, space, parent_title)
    if not parent:
        return None
    parent_id = parent["id"]

    # Search children of parent for our title
    url = f"{base}/rest/api/content/{parent_id}/child/page"
    params = {"expand": "version"}
    r = requests.get(url, params=params, auth=_auth(user, token))
    r.raise_for_status()
    for child in r.json().get("results", []):
        if child.get("title") == title:
            return child
    return None

def create_page(base: str, user: str, token: str, space: str, title: str, body_html: str,
                parent_title: Optional[str] = None) -> Dict[str, Any]:
    payload = {
        "type": "page",
        "title": title,
        "space": {"key": space},
        "body": {"storage": {"value": body_html, "representation": "storage"}}
    }
    if parent_title:
        parent = get_page_by_title(base, user, token, space, parent_title)
        if parent:
            payload["ancestors"] = [{"id": parent["id"]}]
    url = f"{base}/rest/api/content"
    r = requests.post(url, auth=_auth(user, token), json=payload)
    r.raise_for_status()
    return r.json()

def update_page(base: str, user: str, token: str, page_id: str, title: str, body_html: str, version: int) -> Dict[str, Any]:
    url = f"{base}/rest/api/content/{page_id}"
    payload = {
        "id": page_id,
        "type": "page",
        "title": title,
        "version": {"number": version + 1},
        "body": {"storage": {"value": body_html, "representation": "storage"}}
    }
    r = requests.put(url, auth=_auth(user, token), json=payload)
    r.raise_for_status()
    return r.json()

def attach_file(base: str, user: str, token: str, page_id: str, file_path: str) -> Dict[str, Any]:
    url = f"{base}/rest/api/content/{page_id}/child/attachment"
    headers = {"X-Atlassian-Token": "no-check"}
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f)}
        r = requests.post(url, auth=_auth(user, token), headers=headers, files=files)
        r.raise_for_status()
        return r.json()

def page_url(base: str, page_id: str) -> str:
    # Atla Cloud: {base}/spaces/<spaceKey>/pages/<id>
    return f"{base}/spaces?@pageId={page_id}"

def upsert_page_with_attachments(base: str, user: str, token: str,
                                 space: str, title: str, body_html: str,
                                 attachments: List[str], parent_title: Optional[str] = None) -> Tuple[str, str]:
    # Returns (page_id, page_link)
    page = None
    if parent_title:
        page = get_page_by_title_under_parent(base, user, token, space, parent_title, title)
    if not page:
        page = get_page_by_title(base, user, token, space, title)

    if page:
        updated = update_page(base, user, token, page["id"], title, body_html, page["version"]["number"])
        pid = updated["id"]
    else:
        created = create_page(base, user, token, space, title, body_html, parent_title=parent_title)
        pid = created["id"]

    link = page_url(base, pid)

    for fpath in attachments:
        try:
            attach_file(base, user, token, pid, fpath)
            log.info(f"Attached: {fpath}")
        except Exception as e:
            log.warning(f"Attach failed for {fpath}: {e}")

    return pid, link

def main():
    setup_logging()
    read_env()

    base = get_env("CONFLUENCE_BASE", required=True).rstrip("/")
    user = get_env("CONFLUENCE_USER", required=True)
    token = get_env("CONFLUENCE_TOKEN", required=True)
    space = get_env("CONFLUENCE_SPACE", required=True)
    title = get_env("CONFLUENCE_TITLE", required=True)
    parent_title = os.getenv("CONFLUENCE_PARENT_TITLE", "").strip() or None

    # Minimal body; you can customize
    body_html = "<p>Automated upload of Flask Test Result Report.</p>"

    # Attach everything from REPORT_DIR
    report_dir = os.getenv("REPORT_DIR", "report")
    attachments = []
    if os.path.isdir(report_dir):
        for name in os.listdir(report_dir):
            f = os.path.join(report_dir, name)
            if os.path.isfile(f):
                attachments.append(f)

    pid, link = upsert_page_with_attachments(base, user, token, space, title, body_html, attachments, parent_title)
    print(json.dumps({"page_id": pid, "link": link}, indent=2))

if __name__ == "__main__":
    main()
