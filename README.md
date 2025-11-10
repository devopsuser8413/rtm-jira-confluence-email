# RTM → Jenkins → Confluence → Email (Flask Test Results)

Production‑ready pipeline to:
1) Pull **test result attachments** from Jira RTM (by Issue Key or JQL).
2) Publish/update a Confluence page and **attach the report**.
3) Email the report to **multiple recipients** (as attachments) with the Confluence link.

> Works great in Jenkins on Windows or Linux. Uses Python 3.10+.

---

## 📁 Project Structure

```
rtm-jira-confluence-email/
├─ Jenkinsfile
├─ README.md
├─ requirements.txt
├─ .env.example
├─ report/                 # Downloaded test reports (from Jira) + generated artifacts
├─ data/                   # Any extra inputs (kept out of VCS by default)
└─ scripts/
   ├─ pipeline_main.py     # Orchestrates: Jira fetch → Confluence publish → Email
   ├─ fetch_jira_attachments.py
   ├─ confluence_publish.py
   ├─ send_email.py
   └─ utils.py
```

---

## 🔧 Prerequisites

- Python **3.10+**
- A Jira Cloud (or Server/DC) user + API token with **read** access to the RTM issue(s).
- A Confluence user + API token with **create/edit** permissions on the target space.
- SMTP account that can send email to your recipients.
- Jenkins agent with network access to Jira + Confluence + SMTP.

> **Tip (Windows Jenkins):** Python should be on `PATH`. Use a venv inside the workspace (`.venv`).

---

## 🔐 Configuration

You can set everything with **environment variables** in Jenkins or locally via `.env`.

Copy `.env.example` → `.env` and fill in values (or configure Jenkins credentials and map them to env vars).

**Required – Jira**
- `JIRA_BASE` → e.g., `https://your-domain.atlassian.net`
- `JIRA_USER` → Jira account email/username
- `JIRA_TOKEN` → Jira API token (or password for Server/DC)
- **Choose ONE of the following** (the script will prefer `JIRA_ISSUE_KEY` if both exist):
  - `JIRA_ISSUE_KEY` → e.g., `RTM-123`
  - `JIRA_JQL` → e.g., `project = RTM AND issuetype = "Test Plan" ORDER BY created DESC`
- Optional filters:
  - `ATTACH_NAME_CONTAINS` → only download attachments whose name contains this
  - `ATTACH_EXTS` → comma-separated list of file extensions to accept (e.g., `html,pdf,xml`)

**Required – Confluence**
- `CONFLUENCE_BASE` → e.g., `https://your-domain.atlassian.net/wiki`
- `CONFLUENCE_USER`
- `CONFLUENCE_TOKEN`
- `CONFLUENCE_SPACE` → e.g., `DEMO`
- `CONFLUENCE_TITLE` → e.g., `Flask Test Result Report`
- Optional: `CONFLUENCE_PARENT_TITLE` → if you want to create page under a parent

**Required – Email (SMTP)**
- `SMTP_HOST`, `SMTP_PORT` (587 recommended)
- `SMTP_USER`, `SMTP_PASS`
- `REPORT_FROM` → sender email (e.g., `devsecops-bot@yourorg.com`)
- `REPORT_TO` → comma-separated recipients (e.g., `alice@x.com,bob@x.com`)

**General**
- `REPORT_DIR` → defaults to `report`
- `VERSION_FILE` → defaults to `report/version.txt`

---

## ▶️ Local Run

```bash
python -m venv .venv
. .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Create .env from example and fill values
python scripts/pipeline_main.py
```

Outputs:
- Downloads latest matching **test result** attachment(s) from Jira into `report/`.
- Creates/updates Confluence page and **attaches the files**.
- Sends **email** with the attachments and the Confluence page link.
- Increments `report/version.txt` each run.

---

## 🤖 Jenkins Pipeline (Declarative)

- Uses a venv, installs requirements, runs the pipeline, archives the report.
- Designed to work on **Windows or Linux** agents.

> See the `Jenkinsfile` for environment variables and credential bindings.

---

## 🧪 Attachment Selection Logic

- If `ATTACH_NAME_CONTAINS` is set, only attachments whose **filename contains** that substring are downloaded.
- If `ATTACH_EXTS` is set, only those **extensions** will be downloaded.
- If neither is set, we download **all** attachments found on the issue(s).

---

## 🛟 Troubleshooting

- 401/403: Check API token and permissions in Jira/Confluence.
- Nothing downloaded: Verify `JIRA_ISSUE_KEY` or `JIRA_JQL`, and filters.
- Email not delivered: Check SMTP logs, spam policies, and attachment size limits.
- Confluence page duplicate: Same title allowed per space if different parent; otherwise update occurs.

---

## 📄 License

MIT
