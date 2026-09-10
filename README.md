# ResumeFlow Mark 2 (RFM2)

<div align="center">

![ResumeFlow Mark 2](https://img.shields.io/badge/Platform-Swooped.co%20Engine-6366f1?style=for-the-badge&logo=target)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Formats](https://img.shields.io/badge/Formats-Swooped%20PDF-e11d48?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Production%20Ready-emerald?style=for-the-badge)

**Automated Tailored Resume & Cover Letter Generation via [Swooped.co](https://swooped.co) Browser Automation**

[Key Features](#key-features) •
[Architecture](#system-architecture) •
[Installation & Quickstart](#installation--quickstart) •
[Workflow & Usage](#workflow--usage) •
[API Documentation](#api-endpoints) •
[Project Structure](#project-structure)

</div>

---

## Overview

**ResumeFlow Mark 2 (RFM2)** is a specialized automation and document generation suite that interfaces directly with the official **[Swooped.co](https://swooped.co)** platform. 

RFM2 uses a real Chromium browser through Playwright to interact with Swooped's rendered registration, upload, tailoring, and account-management screens. It creates disposable user accounts, uploads your base resume, enters your target company and job description, triggers Swooped's proprietary AI tailoring engines, downloads the actual Swooped-generated **PDF** files locally, and exports those PDF contents to editable **DOCX** files.

---

## Key Features

- 🎯 **100% Native Swooped.co Engine**: All tailoring and cover letter drafting is executed natively by Swooped's proprietary AI models on `https://swooped.co`.
- 🌐 **Real Browser Automation**: Uses Playwright and Chromium to perform the workflow through Swooped's actual web UI instead of calling Swooped's private APIs.
- 📬 **Automated Disposable Temp-Mail Provisioning**: Integrates with disposable mailbox APIs (Mail.tm & 1secmail) for zero personal footprint.
- 📄 **Actual Swooped PDF Output**: Downloads the PDF artifacts produced by Swooped itself. No locally reconstructed or ReportLab placeholder PDFs.
- 📝 **Editable DOCX Exports**: Creates DOCX copies from the extracted text of each actual Swooped PDF for editing.
- 📂 **Organized Local Directory Structure**: Automatically saves your applications under:
  ```text
  downloads/<CompanyName>_<JobRole>/
    ├── <CompanyName>_<JobRole>_Tailored_Resume.pdf
    ├── <CompanyName>_<JobRole>_Tailored_Resume.docx
    ├── <CompanyName>_<JobRole>_Cover_Letter.pdf
    └── <CompanyName>_<JobRole>_Cover_Letter.docx
  ```
- 🔑 **User Credentials Display**: Once generated, your temporary email address and password are displayed in a clean card with **1-click Copy** buttons and a direct link to **[Swooped.co Login](https://swooped.co/auth/login)**, allowing you to log in and inspect your tailored profile directly inside Swooped's official dashboard.
- 🛡️ **User-Controlled On-Demand Account Wiping**: Accounts remain active for your inspection until you decide to delete them. Clicking **"Delete Account on Swooped"** signs in through the browser and uses the account settings screen to permanently wipe all account data.
- 📜 **Account Lifecycle Audit History**: Real-time persistent dashboard tracking all accounts created, target company, role, timestamps, download links, and live deletion statuses.
- 📡 **Real-Time SSE Progress Stream**: Server-Sent Events stream live status, percentages, and log messages across all 6 automation pipeline stages.

---

## System Architecture

```mermaid
graph TD
    User([User in Web Dashboard]) -->|Upload CV + Job Info| FastAPI[FastAPI Server :8000]
    FastAPI -->|SSE Progress| User
    
    subgraph "Automation Core (browser_engine.py)"
        TempMail[Temp-Mail Service] -->|Provision Inbox| Browser[Playwright Chromium Browser]
        Browser -->|Rendered registration and upload UI| BaseRes[Swooped Base Resume Parser]
        BaseRes -->|Rendered job description UI| JobTarget[Job Matching Engine]
        JobTarget -->|Rendered UI| ResumeTailor[Swooped AI Tailored Resume]
        JobTarget -->|Rendered UI| CoverAI[Swooped AI Cover Letter]
    end

    ResumeTailor --> SwoopedDownloads[Actual Swooped PDF Downloads]
    CoverAI --> SwoopedDownloads
    SwoopedDownloads -->|Save actual PDFs| LocalDisk[Local Disk: downloads/Company_Role/]

    FastAPI -->|Show Temp-Mail & Password| CredentialsCard[Credentials Display Card]
    CredentialsCard -->|Manual Inspection| SwoopedDashboard[https://swooped.co/app]
    
    CredentialsCard -->|User clicks Delete| DeleteBrowser[Playwright settings flow]
    DeleteBrowser -->|Wipe Complete| WipedStatus[✓ Account Wiped on Swooped]
```

---

## Installation & Quickstart

### Prerequisites

- **Python 3.10** or higher
- **Git**

### 1. Clone the Repository

```bash
git clone https://github.com/NallukumarRavichandran/resumeFlowMark2.RFM2.git
cd resumeFlowMark2.RFM2
```

### 2. Create and Activate Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**On Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

The workflow runs in Chromium by default. Set `BROWSER_HEADLESS=false` before starting
the app when you want to watch the browser perform each step.

### Optional Browser Use Cloud Session

The repository also retains an optional Browser Use Cloud integration for interactive
remote sessions. It is not used by the default fast pipeline. To enable those optional
session endpoints, create an API key in Browser Use Cloud and configure it on the server:

```bash
export BROWSER_USE_API_KEY="your-browser-use-api-key"
```

The generated result includes an **Open Live Browser** link. Treat that URL as
credential-like and do not share it publicly.

The default dashboard runs the complete operation through a direct local
Playwright Chromium session for lower latency: upload the base resume, enter the
company, role, and job description, then click **Run full Swooped operation**.
The server creates the temporary account, performs the Swooped UI workflow, and
saves the generated files locally. Set `BROWSER_HEADLESS=false` if you want to
watch the browser while it runs.

### 4. Launch Application

```bash
python app.py
```

The application will start on **`http://127.0.0.1:8000`**.

---

## Workflow & Usage

1. Open **`http://127.0.0.1:8000`** in your web browser.
2. **Upload Resume**: Click anywhere on the dashed upload zone or drag & drop your base resume file (`.pdf`, `.docx`, or `.txt`).
3. **Fill Target Job Details**:
   - **Target Company**: e.g., `Google`, `Amazon`, `Konecranes`
   - **Job Title**: e.g., `Product Manager`, `Senior Software Engineer`
   - **Job Description**: Paste the target role's full description or requirements.
4. **Generate**: Click **"Generate on Swooped.co & Download"**.
5. **Real-time Pipeline**: The 6-step timeline will track progress:
   - Step 1: Provision Temp-Mail
   - Step 2: Register on Swooped.co
   - Step 3: Upload Base Resume
   - Step 4: AI Tailoring on Swooped
   - Step 5: Save Swooped PDF Documents
   - Step 6: Credentials Ready (Active)
6. **Inspect on Swooped**: Use the credentials displayed on screen to log into [https://swooped.co/auth/login](https://swooped.co/auth/login) and explore your optimized resume and cover letter on Swooped's platform.
7. **Download Output**: Download your tailored documents directly via the dashboard buttons or click **"Open in Explorer"** to access the local folder.
8. **Wipe Account**: Whenever you are finished, click **"Delete Account on Swooped"** to wipe the account and all associated data permanently.

---

## Project Structure

```text
resumeFlowMark2.RFM2/
├── app.py                     # FastAPI web server with SSE streaming & REST API
├── swooped_engine.py          # Compatibility export for the browser engine
├── browser_engine.py          # Playwright browser workflow for Swooped.co
├── tempmail_service.py        # Disposable temporary email provider (Mail.tm / 1secmail)
├── account_logger.py          # Persistent audit logger for generated accounts
├── test_pipeline.py           # End-to-end integration test against live Swooped APIs
├── requirements.txt           # Python dependencies
├── downloads/                 # Local directory for generated application files
│   └── <Company>_<JobRole>/
│       ├── <Company>_<JobRole>_Tailored_Resume.pdf
│       └── <Company>_<JobRole>_Cover_Letter.pdf
├── logs/
│   └── account_history.json   # Persistent audit history log
└── static/
    ├── index.html             # Responsive dark-mode dashboard interface
    ├── styles.css             # Glassmorphic UI styles matching Swooped brand
    └── app.js                 # Frontend state, drag-and-drop, and SSE handling
```

---

## API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Web dashboard user interface |
| `GET` | `/api/logs` | Fetch all historical account generation and deletion records |
| `POST` | `/api/generate` | Multipart upload starting the live Swooped pipeline (SSE stream) |
| `GET` | `/api/download/{folder}/{file}` | Download generated `.pdf` or `.docx` document |
| `POST` | `/api/open-folder` | Open local folder in OS file explorer |
| `POST` | `/api/delete-account` | Trigger manual on-demand `mutation DeleteUser` on Swooped |

---

## Security & Privacy

- **No Stored Personal Credentials**: No personal Swooped accounts are needed or stored. Every run uses an ephemeral disposable inbox.
- **On-Demand Data Purge**: Unlike automated scripts that leave orphan profiles, RFM2 gives you the tools to purge your data from Swooped servers with a single click.
- **Local Storage**: All generated resumes and cover letters are stored strictly on your local machine under `downloads/`.

---

## License

This project is released under the [MIT License](LICENSE).
