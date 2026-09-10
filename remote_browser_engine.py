import os
import re
import tempfile
import time
import uuid

import requests

from account_logger import AccountLogger
from tempmail_service import TempMailService


DOWNLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")


class RemoteBrowserError(RuntimeError):
    """Raised when Browser Use Cloud cannot start or complete a remote browser run."""


class RemoteBrowserSwoopedEngine:
    """Runs Swooped through a Browser Use Cloud V4 live browser session."""

    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback or (lambda step, total, msg, data=None: None)

    def log_progress(self, step, total, message, extra=None):
        print(f"[{step}/{total}] {message}")
        self.progress_callback(step, total, message, extra)

    @staticmethod
    def _client():
        if not os.getenv("BROWSER_USE_API_KEY"):
            raise RemoteBrowserError(
                "BROWSER_USE_API_KEY is not configured. Create a Browser Use Cloud API key "
                "and export it before starting ResumeFlow."
            )
        try:
            from browser_use_sdk.v4 import BrowserUse
        except ImportError as exc:
            raise RemoteBrowserError(
                "browser-use-sdk is required. Install the project requirements first."
            ) from exc
        return BrowserUse()

    @staticmethod
    def _download_workspace_files(client, workspace_id, target_folder):
        files = client.workspaces.files(workspace_id, include_urls=True)
        downloaded = {}
        for item in files.files:
            if not item.url or not item.path.lower().endswith((".pdf", ".docx")):
                continue
            filename = os.path.basename(item.path)
            response = requests.get(item.url, timeout=60)
            response.raise_for_status()
            path = os.path.join(target_folder, filename)
            with open(path, "wb") as output:
                output.write(response.content)
            downloaded[filename] = path
        return downloaded

    @staticmethod
    def _live_view_url(client, run):
        events = client.runs.events(run.id, limit=100)
        for event in events.events:
            if event.type == "browser.ready":
                return event.data.get("live_view_url")
        return None

    def execute_pipeline(self, resume_bytes, filename, company_name, job_title, job_description):
        run_id = uuid.uuid4().hex[:8]
        clean_company = re.sub(r"[^a-zA-Z0-9_\- ]", "", company_name or "Company").strip().replace(" ", "_")
        clean_role = re.sub(r"[^a-zA-Z0-9_\- ]", "", job_title or "Role").strip().replace(" ", "_")
        folder_name = f"{clean_company}_{clean_role}"
        target_folder = os.path.join(DOWNLOADS_DIR, folder_name)
        os.makedirs(target_folder, exist_ok=True)
        AccountLogger.add_or_update_log(
            run_id, company_name=company_name, job_title=job_title,
            status="Starting remote browser", folder_path=target_folder
        )

        email_account = TempMailService.generate_account()
        email = email_account["email"]
        password = email_account["password"]
        AccountLogger.add_or_update_log(run_id, email=email, password=password, status="Temp-Mail Created")
        self.log_progress(1, 6, "Generating disposable Temp-Mail account...")

        upload_dir = tempfile.mkdtemp(prefix="resumeflow-")
        upload_path = os.path.join(upload_dir, os.path.basename(filename) or "resume.pdf")
        with open(upload_path, "wb") as upload:
            upload.write(resume_bytes)
        try:
            with self._client() as client:
                workspace = client.workspaces.create(name=f"resumeflow-{run_id}")
                client.workspaces.upload(workspace.id, upload_path)
                task = f"""
Use the live browser to complete this Swooped workflow. Do not call Swooped APIs directly.
Open https://swooped.co, accept cookies if shown, and create an account using:
Email: {email}
Password: {password}

Then upload the attached resume file ({filename}), create a tailored application for:
Company: {company_name}
Job title: {job_title}
Job description:
{job_description}

Generate both the tailored resume and cover letter through the visible Swooped UI.
Download the generated PDF and DOCX files into the Browser Use workspace using clear names:
{clean_company}_{clean_role}_Tailored_Resume.pdf
{clean_company}_{clean_role}_Tailored_Resume.docx
{clean_company}_{clean_role}_Cover_Letter.pdf
{clean_company}_{clean_role}_Cover_Letter.docx
Leave the browser session open on the generated documents or account dashboard so the user
can inspect it. Report the current page and whether each file was downloaded.
"""
                self.log_progress(2, 6, "Starting the remote Swooped browser session...")
                run = client.runs.create(task, workspace_id=workspace.id)
                self.log_progress(3, 6, "Remote browser is operating Swooped through its visible UI...")
                result = client.runs.wait_for_completion(run.id)
                self.log_progress(4, 6, "Swooped generation completed in the remote browser...")
                downloaded = self._download_workspace_files(client, workspace.id, target_folder)
                live_view_url = self._live_view_url(client, run)

                if not downloaded:
                    raise RemoteBrowserError(
                        "The remote browser completed without downloading PDF or DOCX files."
                    )

                self.log_progress(5, 6, "Retrieving generated documents from the remote workspace...")
                self.log_progress(6, 6, "Remote browser session is ready for inspection.")
                payload = {
                    "run_id": run_id,
                    "email": email,
                    "password": password,
                    "folder_name": folder_name,
                    "folder_path": target_folder,
                    "live_view_url": live_view_url,
                    "browser_session_id": run.session_id,
                    "browser_use_run_id": run.id,
                    "remote_result": getattr(result, "result", str(result)),
                    "account_deleted": False,
                }
                AccountLogger.add_or_update_log(
                    run_id, status="Active (Remote Browser Ready)", **payload, deleted=False
                )
                return {"success": True, **payload}
        except Exception as exc:
            AccountLogger.add_or_update_log(run_id, status=f"Failed: {exc}")
            self.log_progress(0, 0, f"Remote browser error: {exc}")
            raise
        finally:
            os.unlink(upload_path)
            os.rmdir(upload_dir)

    @classmethod
    def delete_account_by_id(cls, run_id):
        target = next((item for item in AccountLogger.get_logs() if item.get("id") == run_id), None)
        if not target or not target.get("browser_session_id"):
            return {"success": False, "error": "Remote browser session was not found"}
        engine = cls()
        try:
            with engine._client() as client:
                follow_up = client.runs.create(
                    "Delete the current Swooped account through the visible account settings UI. "
                    "Confirm the deletion and report the result.",
                    session_id=target["browser_session_id"],
                )
                result = client.runs.wait_for_completion(follow_up.id)
            AccountLogger.add_or_update_log(run_id, status="Deleted on Swooped", deleted=True)
            return {"success": True, "message": getattr(result, "result", "Account deleted")}
        except Exception as exc:
            AccountLogger.add_or_update_log(run_id, status=f"Delete Failed: {exc}")
            return {"success": False, "error": str(exc)}
