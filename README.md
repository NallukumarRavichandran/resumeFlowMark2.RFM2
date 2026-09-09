# ResumeFlow Mark 2 (RFM2)

> **Automated Tailored Resume & Cover Letter Generation via Direct Swooped.co Integration**

ResumeFlow Mark 2 directly automates the official **[Swooped.co](https://swooped.co)** platform. It provisions disposable temporary email accounts, signs up to Swooped, uploads your base resume, inputs target company and job details, triggers Swooped's own AI resume tailoring and cover letter engines, downloads the outputs strictly as **PDF (`.pdf`)** and **Word Document (`.docx`)** files into an organized local directory, and automatically wipes/deletes the account on Swooped.co upon completion.

---

## Key Features

- **Direct Swooped.co Engine**: 100% of resume optimization and cover letter generation is performed directly on `https://swooped.co` servers.
- **Disposable Temp-Mail Automation**: Automatically provisions real temporary mailboxes (via Mail.tm / 1secmail) for zero-trace operation.
- **No Headless Browser Overhead**: Communicates directly through Firebase Auth and Swooped's Apollo GraphQL APIs (`api.swooped.co`), ensuring high speed and reliability.
- **PDF & Word (.docx) Only**: Outputs strictly formatted ATS-standard Microsoft Word `.docx` and printable `.pdf` documents (no HTML files).
- **Company & Role Organization**: Files are saved into dedicated local folders:
  ```
  downloads/<CompanyName>_<JobRole>/
    ├── <CompanyName>_<JobRole>_Tailored_Resume.pdf
    ├── <CompanyName>_<JobRole>_Tailored_Resume.docx
    ├── <CompanyName>_<JobRole>_Cover_Letter.pdf
    └── <CompanyName>_<JobRole>_Cover_Letter.docx
  ```
- **Post-Generation Account Wiping**: Automatically executes `mutation DeleteUser` on Swooped.co (matching `swooped.co/app/user/delete`) right after download.
- **Account Lifecycle Logs & Audit History**: Persistent dashboard table tracking all accounts created, target company, role, timestamps, and direct download buttons.

---

## Quickstart Guide

### 1. Install Dependencies
Ensure you are using the repository's virtual environment:
```bash
# Activate virtual environment
.\.venv\Scripts\activate

# Install requirements (if not already installed)
pip install -r requirements.txt
```

### 2. Launch the Web Application
```bash
python app.py
```
Open your browser to: **`http://localhost:8000`**

### 3. Usage
1. Drag and drop your base resume (`.pdf`, `.docx`, or `.txt`).
2. Enter the **Target Company** (e.g. `Facebook`) and **Job Title** (e.g. `Product Manager`).
3. Paste the target **Job Description**.
4. Click **"Generate on Swooped.co & Download"**.
5. Watch the live 6-step progress bar as it registers, uploads, tailors, downloads, and cleans up on Swooped.co.
6. Open your local folder or download `.pdf` and `.docx` files directly from the dashboard!
