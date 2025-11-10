
# 🧩 RTM Jira → Jenkins → Confluence → Email Automation Pipeline

This project automates the **end-to-end test result reporting workflow** — fetching RTM test result attachments from Jira, publishing them to Confluence, and sending report notifications to multiple email recipients through Jenkins CI pipeline.

---

## 🧱 1. Software Installation Requirements

### 🖥️ Local / Jenkins Node Setup
Ensure the following are installed and configured on the Jenkins node (Windows/Linux):

| Software | Version | Description |
|-----------|----------|--------------|
| Python | 3.10+ | Required for automation scripts |
| Git | latest | For SCM checkout |
| Jenkins | 2.440+ | CI/CD pipeline engine |
| Pip | latest | Python dependency management |
| Virtualenv | latest | Python virtual environment tool |

### 📦 Required Python Packages
All Python dependencies are declared in `requirements.txt`:

```
requests==2.32.3
python-dotenv==1.0.1
tabulate==0.9.0
fpdf2==2.8.1
certifi>=2024.7.4
```

Install manually for local testing:
```bash
pip install -r requirements.txt
```

---

## 📁 2. Project Structure

```
rtm-jira-confluence-email/
│
├── Jenkinsfile
├── requirements.txt
├── report/
│   ├── version.txt
│   ├── .gitkeep
│
├── scripts/
│   ├── fetch_jira_attachments.py
│   ├── confluence_publish.py
│   ├── send_email.py
│   ├── pipeline_main.py
│   └── utils.py
│
└── .gitignore
```

### 🧩 Folder Summary
- `scripts/`: Core automation logic for Jira, Confluence, and Email.
- `report/`: Generated test results and version tracking.
- `Jenkinsfile`: Declarative Jenkins pipeline definition.

---

## 🚀 3. Jenkins Pipeline Stages Overview

| Stage | Purpose |
|--------|----------|
| **Checkout Repository** | Pulls latest code from GitHub |
| **Set up Python Virtual Environment** | Creates `.venv`, installs dependencies |
| **Run: Jira → Confluence → Email** | Executes end-to-end automation script |
| **Archive Reports** | Stores test result files as Jenkins artifacts |
| **Send Jenkins Email Notification** | Sends additional Jenkins-level notification |

---

## 🔐 4. API Token & App Password Creation

### ✅ Jira Cloud API Token
1. Log in to [https://id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **Create API Token**
3. Copy and store the token securely
4. Use the token for Jenkins credentials named `jira-token`

### ✅ Confluence Cloud API Token
Confluence and Jira share the same token source.  
Use the same Atlassian API token for `confluence-token` credentials.

### ✅ Gmail App Password (for SMTP)
1. Visit [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Create an App Password for **Mail** → **Windows Computer**
3. Use this as `smtp-pass` credential in Jenkins.

---

## ⚙️ 5. Jenkins Setup Instructions

### 🔌 Required Jenkins Plugins
Install via **Manage Jenkins → Plugins → Available Plugins**:
- **Pipeline** (Declarative + Groovy)
- **Email Extension Plugin**
- **Credentials Binding Plugin**
- **Git Plugin**
- **AnsiColor Plugin**

### 🧾 SMTP Configuration
1. Navigate to **Manage Jenkins → System → Extended E-mail Notification**
2. Configure:
   - SMTP Server: `smtp.gmail.com`
   - Port: `587`
   - Credentials: `smtp-user` and `smtp-pass`
   - Use TLS: ✅ checked
3. Test connection.

### 🔑 Jenkins Credentials Setup
Create credentials for the following under **Manage Jenkins → Credentials → Global**:

| ID | Type | Example Value |
|----|------|----------------|
| `jira-base` | Secret Text | `https://your-domain.atlassian.net` |
| `jira-user` | Username with Password | `yourname@company.com` |
| `jira-token` | Secret Text | `JIRA_API_TOKEN` |
| `confluence-base` | Secret Text | `https://your-domain.atlassian.net/wiki` |
| `confluence-user` | Username with Password | `yourname@company.com` |
| `confluence-token` | Secret Text | `CONFLUENCE_API_TOKEN` |
| `smtp-host` | Secret Text | `smtp.gmail.com` |
| `smtp-user` | Username with Password | `youremail@gmail.com` |
| `smtp-pass` | Secret Text | `GMAIL_APP_PASSWORD` |
| `sender-email` | Secret Text | `youremail@gmail.com` |
| `multi-receivers` | Secret Text | `devops@company.com,qa@company.com` |

---

## 🔁 6. Pipeline Stage Explanation

### 🧩 Stage 1 – Checkout Repository
- Pulls the latest code from the GitHub repo using Jenkins credentials.
- Ensures the latest pipeline and scripts are used.

### 🧩 Stage 2 – Setup Python Virtual Environment
- Creates `.venv` directory.
- Installs Python dependencies from `requirements.txt`.

### 🧩 Stage 3 – Run: Jira → Confluence → Email
- Executes the automation sequence:
  1. **Fetch from Jira** – Downloads RTM test result attachments.
  2. **Publish to Confluence** – Creates a new versioned page, uploads attachments, and embeds the attachments macro.
  3. **Send Email** – Sends test report summary to multiple recipients.

### 🧩 Stage 4 – Archive Reports
- Archives all generated reports (`.html`, `.pdf`, `.txt`) for future download in Jenkins UI.

### 🧩 Stage 5 – Send Jenkins Email Notification
- Sends an HTML-formatted email summarizing build status and Confluence page link.

---

## 🧰 7. Troubleshooting & Diagnostics

| Issue | Root Cause | Resolution |
|--------|-------------|-------------|
| ❌ Attachments not visible in Confluence | Attachments uploaded but macro missing | Ensure `<ac:structured-macro ac:name="attachments">` added in page body |
| ⚠️ “Not sent to the following valid addresses” | Jenkins SMTP not authenticated | Verify “Use SMTP Authentication” and correct App Password |
| ❌ Jira 403 Unauthorized | API Token not linked to account | Regenerate Jira token under same Atlassian account |
| ❌ Confluence 404 | Wrong BASE URL | Use `/wiki` suffix (e.g., `https://yourcompany.atlassian.net/wiki`) |
| ❌ `requests.exceptions.SSLError` | Certificate verification issue | Add `certifi>=2024.7.4` in requirements.txt |
| ❌ Python Unicode Errors | Windows terminal encoding | Add `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` to Jenkinsfile |

---

## 📊 8. Output Artifacts

After successful pipeline execution:
- Reports uploaded to Confluence (`Flask Test Result Report vX`)
- Files visible under “Attachments” section.
- Emails sent to configured receivers.
- Artifacts archived under Jenkins “Build Artifacts” tab.

---

## 🧠 9. Versioning

Each pipeline run automatically increments the report version (`v1`, `v2`, …).  
This is tracked via `report/version.txt`.

---

## 🧩 10. References

- [Jira REST API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/)
- [Confluence REST API](https://developer.atlassian.com/cloud/confluence/rest/v1/intro/)
- [Jenkins Pipeline Syntax](https://www.jenkins.io/doc/book/pipeline/syntax/)
- [Gmail App Password Guide](https://support.google.com/mail/answer/185833)

---

✅ **Author:** DevOpsUser8413  
📅 **Last Updated:** November 2025  
🏗️ **Purpose:** Enterprise-grade DevSecOps RTM Integration CI/CD Automation.
