\
import os
import json
import mimetypes
import smtplib
import logging
from email.message import EmailMessage
from typing import List

from utils import setup_logging, read_env, get_env

log = logging.getLogger("email")

def send_email_with_attachments(
    host: str,
    port: int,
    user: str,
    password: str,
    sender: str,
    recipients: List[str],
    subject: str,
    body: str,
    attachments: List[str],
):
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content(body)

    for path in attachments:
        ctype, encoding = mimetypes.guess_type(path)
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        with open(path, "rb") as f:
            msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=os.path.basename(path))

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(msg)

def main():
    setup_logging()
    read_env()

    host = get_env("SMTP_HOST", required=True)
    port = int(get_env("SMTP_PORT", "587"))
    smtp_user = get_env("SMTP_USER", required=True)
    smtp_pass = get_env("SMTP_PASS", required=True)
    sender = get_env("REPORT_FROM", required=True)
    recipients = [s.strip() for s in get_env("REPORT_TO", required=True).split(",") if s.strip()]

    confluence_link = os.getenv("CONFLUENCE_PAGE_LINK", "").strip()
    subject = f"[Automated] Flask Test Result Report"
    body = "Please find the test result report attached."
    if confluence_link:
        body += f"\nConfluence: {confluence_link}"

    report_dir = os.getenv("REPORT_DIR", "report")
    attachments = []
    if os.path.isdir(report_dir):
        for name in os.listdir(report_dir):
            f = os.path.join(report_dir, name)
            if os.path.isfile(f):
                attachments.append(f)

    send_email_with_attachments(host, port, smtp_user, smtp_pass, sender, recipients, subject, body, attachments)
    print(json.dumps({"recipients": recipients, "attachments": attachments}, indent=2))

if __name__ == "__main__":
    main()
