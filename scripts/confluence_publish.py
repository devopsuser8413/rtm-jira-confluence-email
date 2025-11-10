import os
import json
import logging
import mimetypes
import requests
from typing import List, Dict, Any, Optional
from utils import setup_logging, read_env, get_env

log = logging.getLogger("confluence_publish")


# --------------------------------------------------------------------
# Authentication Helper
# --------------------------------------------------------------------
def _auth(user: str, token: str):
    return (user, token)


# --------------------------------------------------------------------
# Page Handling
# --------------------------------------------------------------------
def get_page_by_title(base: str, user: str, token: str, space: str, title: str) -> Optional[Dict[str, Any]]:
    url = f"{base}/rest/api/content"
    params = {"spaceKey": space, "title": title, "expand": "version,ancestors"}
    r = requests.get(url, params=params, auth=_auth(user, token))
    r.raise_for_status()
    results = r.json().get("results", [])
    return results[0] if results else None


def create_page(base: str, user: str, token: str, space: str, title: str, body_html: str,
                parent_title: Optional[str] = None) -> Dict[str, Any]:
    """Create a new Confluence page under an optional parent."""
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
        else:
            log.warning(f"⚠️ Parent page '{parent_title}' not found. Creating at space root.")

    url = f"{base}/rest/api/content"
    r = requests.post(url, auth=_auth(user, token), json=payload)
    if not r.ok:
        log.error(f"❌ Failed to create page: {r.status_code} {r.text}")
    r.raise_for_status()

    created = r.json()
    log.info(f"✅ Created new Confluence page: {title} (ID: {created.get('id')})")
    return created


# --------------------------------------------------------------------
# Attachment Handling
# --------------------------------------------------------------------
def attach_file(base: str, user: str, token: str, page_id: str, file_path: str):
    """Upload file as attachment to a Confluence Cloud page."""
    headers = {"X-Atlassian-Token": "no-check"}
    url = f"{base}/rest/api/content/{page_id}/child/attachment"

    file_path = os.path.normpath(file_path)
    filename = os.path.basename(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    mime_type = mime_type or "application/octet-stream"

    with open(file_path, "rb") as f:
        files = {"file": (filename, f, mime_type)}
        r = requests.post(url, auth=_auth(user, token), headers=headers, files=files)
        if not r.ok:
            log.error(f"❌ Attachment upload failed for {filename}: {r.status_code} {r.text}")
        else:
            log.info(f"📎 Uploaded attachment: {filename}")
        r.raise_for_status()


# --------------------------------------------------------------------
# Utilities
# --------------------------------------------------------------------
def page_url(base: str, page_id: str, space: str) -> str:
    return f"{base}/spaces/{space}/pages/{page_id}"


def next_version_number(version_file: str = "report/version.txt") -> int:
    os.makedirs(os.path.dirname(version_file), exist_ok=True)
    if os.path.exists(version_file):
        try:
            with open(version_file) as f:
                return int(f.read().strip()) + 1
        except Exception:
            pass
    return 1


def write_version(version_file: str, version: int):
    with open(version_file, "w") as f:
        f.write(str(version))


# --------------------------------------------------------------------
# Main Execution
# --------------------------------------------------------------------
def main():
    setup_logging()
    read_env()

    base = get_env("CONFLUENCE_BASE", required=True).rstrip("/")
    user = get_env("CONFLUENCE_USER", required=True)
    token = get_env("CONFLUENCE_TOKEN", required=True)
    space = get_env("CONFLUENCE_SPACE", required=True)
    title = get_env("CONFLUENCE_TITLE", required=True)
    parent_title = os.getenv("CONFLUENCE_PARENT_TITLE", "").strip() or None

    report_dir = os.getenv("REPORT_DIR", "report")
    version_file = os.path.join(report_dir, "version.txt")

    version = next_version_number(version_file)
    write_version(version_file, version)
    versioned_title = f"{title} v{version}"

    # 🧩 Updated HTML body: includes the attachments macro
    body_html = f"""
    <p><b>Automated Test Result Report</b> for version <b>v{version}</b>.</p>
    <p>Generated automatically by Jenkins CI pipeline.</p>
    <p>Below are all attached test result files:</p>
    <ac:structured-macro ac:name="attachments"></ac:structured-macro>
    """

    # Create new Confluence page
    page = create_page(base, user, token, space, versioned_title, body_html, parent_title)
    page_id = page.get("id")
    link = page_url(base, page_id, space)
    log.info(f"🌐 Confluence Page URL: {link}")

    # Upload report files
    if not os.path.isdir(report_dir):
        log.warning(f"⚠️ Report directory not found: {report_dir}")
    else:
        for name in os.listdir(report_dir):
            fpath = os.path.join(report_dir, name)
            if os.path.isfile(fpath) and not name.endswith(".gitkeep"):
                try:
                    attach_file(base, user, token, page_id, fpath)
                except Exception as e:
                    log.error(f"❌ Failed to attach {name}: {e}")

    print(json.dumps({"page_id": page_id, "link": link, "version": version}, indent=2))


if __name__ == "__main__":
    main()
