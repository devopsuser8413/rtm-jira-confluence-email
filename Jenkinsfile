pipeline {
    agent any

    options {
        timestamps()
        ansiColor('xterm')
        disableConcurrentBuilds()
    }

    environment {
        // =============================
        // 🔒 Jira Configuration
        // =============================
        JIRA_BASE   = credentials('jira-base')
        JIRA_USER   = credentials('jira-user')
        JIRA_TOKEN  = credentials('jira-token')

        // =============================
        // 📘 Confluence Configuration
        // =============================
        CONFLUENCE_BASE  = credentials('confluence-base')
        CONFLUENCE_USER  = credentials('confluence-user')
        CONFLUENCE_TOKEN = credentials('confluence-token')
        CONFLUENCE_SPACE = 'DEMO'
        CONFLUENCE_TITLE = 'Flask Test Result Report'
        CONFLUENCE_PARENT_TITLE = 'Automation Reports'

        // =============================
        // ✉️ SMTP / Email Configuration
        // =============================
        SMTP_HOST   = credentials('smtp-host')
        SMTP_PORT   = '587'
        SMTP_USER   = credentials('smtp-user')
        SMTP_PASS   = credentials('smtp-pass')
        REPORT_FROM = credentials('sender-email')
        REPORT_TO   = credentials('multi-receivers')

        // =============================
        // ⚙️ General Configuration
        // =============================
        REPORT_DIR   = 'report'
        VERSION_FILE = 'report/version.txt'
        PYTHONUTF8   = '1'
        PYTHONIOENCODING = 'utf-8'
        VENV_PATH    = '.venv'
    }

    parameters {
        string(name: 'JIRA_ISSUE_KEY', defaultValue: '', description: 'RTM Issue Key (e.g., RTM-123)')
        string(name: 'JIRA_JQL', defaultValue: '', description: 'Optional JQL query if ISSUE_KEY not set')
        string(name: 'ATTACH_NAME_CONTAINS', defaultValue: 'report', description: 'Filter by filename substring')
        string(name: 'ATTACH_EXTS', defaultValue: 'html,pdf,xml', description: 'Allowed extensions')
    }

    stages {

        // -------------------------------------------------
        stage('Checkout Repository') {
            steps {
                echo '📥 Checking out repository...'
                checkout scm
            }
        }

        // -------------------------------------------------
        stage('Set up Python Virtual Environment') {
            steps {
                bat '''
                    echo =========================================
                    echo 🐍 Setting up Python Virtual Environment
                    echo =========================================
                    python -m venv "%VENV_PATH%"
                    call "%VENV_PATH%\\Scripts\\activate"
                    python -m pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        // -------------------------------------------------
        stage('Run: Jira → Confluence → Email') {
            steps {
                bat '''
                    echo =========================================
                    echo 🚀 Running Automation Pipeline
                    echo =========================================
                    call "%VENV_PATH%\\Scripts\\activate"

                    rem --- Fetch Jira RTM attachments ---
                    python scripts\\fetch_jira_attachments.py

                    rem --- Publish to Confluence (creates new versioned page & attaches reports) ---
                    python scripts\\confluence_publish.py

                    rem --- Send SMTP email with attached report ---
                    python scripts\\send_email.py
                '''
            }
        }

        // -------------------------------------------------
        stage('Archive Reports') {
            steps {
                echo '📦 Archiving generated reports...'
                archiveArtifacts artifacts: 'report/*.*', fingerprint: true, allowEmptyArchive: true
            }
        }

        // -------------------------------------------------
        stage('Send Jenkins Email Notification') {
            steps {
                script {
                    def recipients = env.REPORT_TO.replace(',', ' ')
                    def version = readFile(env.VERSION_FILE).trim()

                    emailext(
                        subject: "✅ [Jenkins] Flask Test Report v${version}",
                        to: recipients,
                        from: env.REPORT_FROM,
                        body: """
                            <h2>Automated Test Result Report Published</h2>
                            <p>Dear Team,</p>
                            <p>The latest <b>Flask Test Result Report</b> (v${version}) has been successfully published.</p>
                            <p><b>Confluence Page:</b> ${env.CONFLUENCE_BASE}/display/${env.CONFLUENCE_SPACE}/${env.CONFLUENCE_TITLE.replace(' ', '+')}+v${version}</p>
                            <p>Build URL: <a href="${env.BUILD_URL}">${env.BUILD_URL}</a></p>
                            <p>Artifacts archived under: <code>${env.REPORT_DIR}</code></p>
                            <br>
                            <p>Regards,<br><b>Jenkins DevSecOps Bot</b></p>
                        """,
                        mimeType: 'text/html'
                    )
                }
            }
        }
    }

    post {
        success {
            echo '✅ Pipeline completed successfully — report published and emails sent.'
        }
        failure {
            echo '❌ Pipeline failed. Check Jenkins logs for details.'
            script {
                emailext(
                    subject: "❌ [FAILED] Flask Test Report Pipeline - ${env.BUILD_NUMBER}",
                    to: env.REPORT_TO.replace(',', ' '),
                    from: env.REPORT_FROM,
                    body: """
                        <h2>Pipeline Failed</h2>
                        <p>Please review the console logs for detailed error messages.</p>
                        <p>Build URL: <a href="${env.BUILD_URL}">${env.BUILD_URL}</a></p>
                    """,
                    mimeType: 'text/html'
                )
            }
        }
    }
}
