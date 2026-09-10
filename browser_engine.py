import os
import re
import tempfile
import time
import uuid
from contextlib import contextmanager

from docx import Document
from pypdf import PdfReader

from account_logger import AccountLogger
from tempmail_service import TempMailService


DOWNLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
PREVIEWS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "browser_previews")
SWOOPED_URL = "https://swooped.co"
os.makedirs(PREVIEWS_DIR, exist_ok=True)


class BrowserAutomationError(RuntimeError):
    """Raised when the Swooped browser flow cannot find a required UI control."""


class BrowserSwoopedEngine:
    """Runs the Swooped workflow through its rendered website using Playwright."""

    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback or (lambda step, total, msg, data=None: None)

    def log_progress(self, step, total, message, extra=None):
        print(f"[{step}/{total}] {message}")
        self.progress_callback(step, total, message, extra)

    @staticmethod
    def _capture_preview(page, run_id, label):
        filename = f"{run_id}_{label}.png"
        path = os.path.join(PREVIEWS_DIR, filename)
        page.screenshot(path=path)
        return f"/api/browser-preview/{filename}"

    @staticmethod
    def _convert_downloaded_pdf_to_docx(pdf_path, docx_path):
        text = "\n".join(
            page.extract_text() or "" for page in PdfReader(pdf_path).pages
        ).strip()
        if not text:
            raise BrowserAutomationError(
                f"Downloaded Swooped PDF contains no extractable text: {os.path.basename(pdf_path)}"
            )
        document = Document()
        for line in text.splitlines():
            if line.strip():
                document.add_paragraph(line.strip())
        document.save(docx_path)

    @staticmethod
    def _headless():
        return os.getenv("BROWSER_HEADLESS", "true").lower() not in {"0", "false", "no"}

    @staticmethod
    def _click_first(page, labels, timeout=5000):
        for label in labels:
            locator = page.get_by_role("button", name=re.compile(label, re.I))
            if locator.count():
                locator.first.click(timeout=timeout)
                return
            locator = page.get_by_role("link", name=re.compile(label, re.I))
            if locator.count():
                locator.first.click(timeout=timeout)
                return
        raise BrowserAutomationError(f"Could not find a Swooped control matching: {', '.join(labels)}")

    @staticmethod
    def _dismiss_cookies(page):
        consent = page.get_by_role("button", name=re.compile(r"accept", re.I))
        if consent.count():
            consent.first.click(timeout=3000)

    @staticmethod
    def _fill_first(page, labels, value, timeout=5000):
        for label in labels:
            locator = page.get_by_label(re.compile(label, re.I))
            if locator.count():
                locator.first.fill(value, timeout=timeout)
                return
            locator = page.locator(
                f'input[name*="{label.lower()}"], textarea[name*="{label.lower()}"], '
                f'input[placeholder*="{label.lower()}"], textarea[placeholder*="{label.lower()}"]'
            )
            if locator.count():
                locator.first.fill(value, timeout=timeout)
                return
        normalized_labels = [
            re.sub(r"[^a-z0-9]", "", label.lower()) for label in labels
        ]
        fields = page.locator("input, textarea")
        for index in range(fields.count()):
            field = fields.nth(index)
            metadata = " ".join(
                filter(
                    None,
                    [
                        field.get_attribute("name"),
                        field.get_attribute("id"),
                        field.get_attribute("placeholder"),
                        field.get_attribute("aria-label"),
                    ],
                )
            )
            normalized_metadata = re.sub(r"[^a-z0-9]", "", metadata.lower())
            if any(label in normalized_metadata for label in normalized_labels):
                field.fill(value, timeout=timeout)
                return
        raise BrowserAutomationError(f"Could not find a Swooped field matching: {', '.join(labels)}")

    @contextmanager
    def _browser(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise BrowserAutomationError(
                "Playwright is required. Install requirements.txt and run "
                "'python -m playwright install chromium'."
            ) from exc

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self._headless())
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()
            try:
                yield page
            finally:
                context.close()
                browser.close()

    def _register(self, page, email, password):
        last_state = ""
        for attempt in range(3):
            page.goto(f"{SWOOPED_URL}/auth/register", wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
            self._dismiss_cookies(page)
            self._fill_first(page, ["email"], email)
            self._fill_first(page, ["password"], password)
            self._fill_first(page, ["password confirmation", "confirm password"], password)
            agreement = page.get_by_label(re.compile(r"terms of service|privacy policy", re.I))
            if agreement.count() and not agreement.first.is_checked():
                agreement.first.check()
            self._click_first(page, ["create account", "sign up", "get started", "register"], timeout=10000)
            page.wait_for_timeout(1500)
            if "/auth/register" in page.url:
                form = page.locator("form")
                if form.count():
                    form.evaluate("(form) => form.requestSubmit()")
            page.wait_for_timeout(7000)
            if "/auth/login" in page.url:
                page_text = page.locator("body").inner_text()
                if re.search(r"invalid|incorrect|unable|failed|error|verify", page_text, re.I):
                    last_state = page_text[:500]
                    break
                self._login(page, email, password)
            if "/app" not in page.url:
                page.goto(f"{SWOOPED_URL}/app", wait_until="domcontentloaded")
                page.wait_for_timeout(3000)
            if "/auth/login" not in page.url and "/auth/register" not in page.url and "/app" in page.url:
                return
            last_state = page.locator("body").inner_text()[:500]
            if attempt < 2:
                page.wait_for_timeout(2000)
        form_state = page.locator("input").evaluate_all(
            "(inputs) => inputs.map((input) => ({name: input.name, type: input.type, "
            "value: input.type === 'password' ? '<redacted>' : input.value, "
            "checked: input.checked, valid: input.checkValidity()}))"
        )
        raise BrowserAutomationError(
            f"Swooped registration did not complete after 3 attempts at {page.url}. "
            f"Page message: {last_state} Form state: {form_state}"
        )

    def _login(self, page, email, password):
        page.goto(f"{SWOOPED_URL}/auth/login", wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        self._dismiss_cookies(page)
        self._fill_first(page, ["email"], email)
        self._fill_first(page, ["password"], password)
        self._click_first(page, ["log in", "sign in", "login"])
        page.wait_for_load_state("domcontentloaded")

    def _upload_resume(self, page, resume_bytes, filename):
        extension = os.path.splitext(filename)[1].lower()
        if extension not in {".pdf", ".docx"}:
            extension = ".docx"
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
            temp_path = temp_file.name
            if extension == ".docx":
                document = Document()
                for line in resume_bytes.decode("utf-8", errors="replace").splitlines():
                    document.add_paragraph(line)
                document.save(temp_path)
            else:
                temp_file.write(resume_bytes)
        try:
            for upload_url in (f"{SWOOPED_URL}/app", f"{SWOOPED_URL}/app/resumes"):
                page.goto(upload_url, wait_until="domcontentloaded")
                page.wait_for_timeout(5000)
                file_input = page.locator('input[type="file"]')
                if not file_input.count():
                    continue
                file_input.first.set_input_files(temp_path)
                page.wait_for_timeout(8000)
                for label in ["continue", "next", "save and continue", "complete setup"]:
                    control = page.get_by_role("button", name=re.compile(label, re.I))
                    if control.count() and control.first.is_visible():
                        control.first.click(timeout=5000)
                        page.wait_for_timeout(4000)
                        break
                if "You haven't added any resumes" not in page.locator("body").inner_text():
                    return
            raise BrowserAutomationError(
                f"Swooped resume upload did not persist at {page.url}."
            )
        finally:
            os.unlink(temp_path)

    def _create_job_optimized_resume(self, page, company_name, job_title, job_description):
        if "setup_profile_step" in page.url:
            for label in ["continue", "next", "save and continue", "complete setup", "skip"]:
                control = page.get_by_role("button", name=re.compile(label, re.I))
                if control.count() and control.first.is_visible():
                    control.first.click(timeout=5000)
                    page.wait_for_timeout(2500)
                    if "setup_profile_step" not in page.url:
                        break
            page.goto(f"{SWOOPED_URL}/app/resumes", wait_until="domcontentloaded")
            page.wait_for_timeout(4000)
        try:
            self._click_first(
                page,
                ["create (?:a )?job-optimized resume", "job-optimized resume"],
                timeout=10000,
            )
        except BrowserAutomationError as exc:
            raise BrowserAutomationError(
                f"{exc} at {page.url}. Page text: {page.locator('body').inner_text()[:800]}"
            ) from exc
        page.wait_for_timeout(3000)
        if not page.locator("input, textarea").count():
            page.goto(f"{SWOOPED_URL}/app/resumes/create", wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
        try:
            self._fill_first(page, ["company name", "company", "organization", "employer"], company_name)
            self._fill_first(page, ["job title", "role", "position"], job_title)
            self._fill_first(page, ["job description", "description", "job details"], job_description)
        except BrowserAutomationError as exc:
            fields = page.locator("input, textarea").evaluate_all(
                "(nodes) => nodes.map((node) => ({name: node.name, id: node.id, "
                "placeholder: node.placeholder, aria: node.getAttribute('aria-label')}))"
            )
            raise BrowserAutomationError(
                f"{exc} at {page.url}. Fields: {fields}. "
                f"Page text: {page.locator('body').inner_text()[:1000]}"
            ) from exc
        cover_toggle = page.get_by_role("button", name=re.compile("add a cover letter", re.I))
        if cover_toggle.count():
            cover_toggle.first.click()
        self._click_first(page, ["optimize resume"], timeout=10000)
        page.wait_for_timeout(3000)

    def _generate_documents(self, page, company_name, job_title, download_dir):
        page.wait_for_timeout(8000)
        for label in ["generate cover letter", "cover letter"]:
            dialog = page.get_by_role("dialog")
            locator = (
                dialog.get_by_role("button", name=re.compile(label, re.I))
                if dialog.count()
                else page.get_by_role("button", name=re.compile(label, re.I))
            )
            if locator.count():
                locator.first.click()
                page.wait_for_timeout(3000)
                break
        for label in ["Choose Comprehensive Resume", "Choose Focused Resume"]:
            choice = page.get_by_role("button", name=re.compile(label, re.I))
            if choice.count() and choice.first.is_visible():
                choice.first.click(timeout=10000)
                page.wait_for_timeout(10000)
                break
        if "1 task in progress" in page.locator("body").inner_text():
            for _ in range(12):
                page.wait_for_timeout(5000)
                if "task in progress" not in page.locator("body").inner_text().lower():
                    break
        page.goto(f"{SWOOPED_URL}/app/resumes", wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        view_control = page.get_by_role("button", name=re.compile(r"view", re.I))
        if view_control.count() and view_control.first.is_visible():
            view_control.first.click(timeout=10000)
            page.wait_for_timeout(5000)
        for label in ["Resume optimization completed", "Cover letter generation completed"]:
            completed = page.get_by_role("button", name=re.compile(label, re.I))
            if completed.count() and completed.first.is_visible():
                completed.first.click(timeout=5000)
                page.wait_for_timeout(3000)
        body_text = page.locator("body").inner_text()
        if not body_text.strip():
            raise BrowserAutomationError("Swooped returned an empty document page.")
        downloaded = []
        controls = page.locator("a, button")
        for index in range(controls.count()):
            control = controls.nth(index)
            if not control.is_visible():
                continue
            label = (control.inner_text() or "") + " " + (control.get_attribute("aria-label") or "")
            href = control.get_attribute("href") or ""
            if not re.search(r"download|export|pdf|docx|word", f"{label} {href}", re.I):
                continue
            try:
                with page.expect_download(timeout=5000) as download_info:
                    control.click(timeout=5000)
                download = download_info.value
                target_path = os.path.join(download_dir, download.suggested_filename)
                download.save_as(target_path)
                downloaded.append(target_path)
            except Exception:
                continue
        if not downloaded:
            controls_text = controls.evaluate_all(
                "(nodes) => nodes.map((node) => ({tag: node.tagName, text: node.innerText, "
                "aria: node.getAttribute('aria-label'), href: node.getAttribute('href')}))"
            )
            raise BrowserAutomationError(
                "Swooped completed generation but exposed no downloadable resume or cover-letter files. "
                f"Visible controls: {controls_text[:30]}"
            )
        return body_text, downloaded

    def execute_pipeline(self, resume_bytes, filename, company_name, job_title, job_description):
        run_id = uuid.uuid4().hex[:8]
        clean_company = re.sub(r"[^a-zA-Z0-9_\- ]", "", company_name or "Company").strip().replace(" ", "_")
        clean_role = re.sub(r"[^a-zA-Z0-9_\- ]", "", job_title or "Role").strip().replace(" ", "_")
        folder_name = f"{clean_company}_{clean_role}"
        target_folder = os.path.join(DOWNLOADS_DIR, folder_name)
        os.makedirs(target_folder, exist_ok=True)
        for existing_name in (
            f"{folder_name}_Tailored_Resume.pdf",
            f"{folder_name}_Tailored_Resume.docx",
            f"{folder_name}_Cover_Letter.pdf",
            f"{folder_name}_Cover_Letter.docx",
        ):
            existing_path = os.path.join(target_folder, existing_name)
            if os.path.exists(existing_path):
                os.unlink(existing_path)
        AccountLogger.add_or_update_log(
            run_id, company_name=company_name, job_title=job_title,
            status="Starting", folder_path=target_folder
        )

        email_account = None
        try:
            self.log_progress(1, 6, "Generating disposable Temp-Mail account...")
            for attempt in range(3):
                try:
                    email_account = TempMailService.generate_account()
                    break
                except RuntimeError as exc:
                    if attempt == 2:
                        raise
                    time.sleep(2)
            email = email_account["email"]
            password = email_account["password"]
            AccountLogger.add_or_update_log(run_id, email=email, password=password, status="Temp-Mail Created")

            with self._browser() as page:
                self.log_progress(2, 6, f"Registering account on Swooped.co ({email})...")
                self._register(page, email, password)
                preview_url = self._capture_preview(page, run_id, "registered")
                self.progress_callback(2, 6, "Swooped account ready", {"preview_url": preview_url})
                AccountLogger.add_or_update_log(run_id, status="Swooped Registered")

                self.log_progress(3, 6, f"Uploading base resume ({filename}) in the Swooped browser...")
                self._upload_resume(page, resume_bytes, filename)
                preview_url = self._capture_preview(page, run_id, "uploaded")
                self.progress_callback(3, 6, "Resume uploaded in Swooped", {"preview_url": preview_url})

                self.log_progress(4, 6, "Creating the job target and generating documents in Swooped...")
                self._create_job_optimized_resume(page, company_name, job_title, job_description)
                preview_url = self._capture_preview(page, run_id, "generating")
                self.progress_callback(4, 6, "Swooped is generating the application", {"preview_url": preview_url})
                page_text, downloaded_files = self._generate_documents(
                    page, company_name, job_title, target_folder
                )
                preview_url = self._capture_preview(page, run_id, "complete")
                self.progress_callback(5, 6, "Swooped documents are ready", {"preview_url": preview_url})

            cover_letter_text = self._extract_cover_letter(page_text, company_name, job_title)

            self.log_progress(5, 6, "Waiting for Swooped browser generation to complete...")
            time.sleep(1)
            self.log_progress(6, 6, f"Saving actual Swooped PDF documents to {folder_name}...")
            paths = {
                "resume_pdf": os.path.join(target_folder, f"{clean_company}_{clean_role}_Tailored_Resume.pdf"),
                "resume_docx": os.path.join(target_folder, f"{clean_company}_{clean_role}_Tailored_Resume.docx"),
                "cover_pdf": os.path.join(target_folder, f"{clean_company}_{clean_role}_Cover_Letter.pdf"),
                "cover_docx": os.path.join(target_folder, f"{clean_company}_{clean_role}_Cover_Letter.docx"),
            }
            unnamed_pdf_index = 0
            for downloaded_path in downloaded_files:
                lower_name = os.path.basename(downloaded_path).lower()
                if "cover" in lower_name or "letter" in lower_name:
                    destination = paths["cover_pdf"]
                else:
                    destination = paths["resume_pdf"] if unnamed_pdf_index == 0 else paths["cover_pdf"]
                    unnamed_pdf_index += 1
                os.replace(downloaded_path, destination)
            missing = [path for path in (paths["resume_pdf"], paths["cover_pdf"]) if not os.path.exists(path)]
            if missing:
                raise BrowserAutomationError(
                    f"Swooped downloads were incomplete; missing: {', '.join(os.path.basename(path) for path in missing)}. "
                    f"Captured: {[os.path.basename(path) for path in downloaded_files]}; "
                    f"Folder: {os.listdir(target_folder)}"
                )
            self._convert_downloaded_pdf_to_docx(paths["resume_pdf"], paths["resume_docx"])
            self._convert_downloaded_pdf_to_docx(paths["cover_pdf"], paths["cover_docx"])

            AccountLogger.add_or_update_log(
                run_id, status="Active (Awaiting Delete)", email=email, password=password,
                resume_pdf=paths["resume_pdf"], resume_docx=paths["resume_docx"],
                cover_pdf=paths["cover_pdf"], cover_docx=paths["cover_docx"], deleted=False
            )
            result = {
                "run_id": run_id, "email": email, "password": password,
                "folder_name": folder_name, "folder_path": target_folder, "account_deleted": False,
                "cover_letter_text": cover_letter_text,
            }
            self.log_progress(6, 6, "Generation completed through the real Swooped browser.", result)
            return {"success": True, **result}
        except Exception as exc:
            AccountLogger.add_or_update_log(run_id, status=f"Failed: {exc}")
            self.log_progress(0, 0, f"Error: {exc}")
            raise

    @staticmethod
    def _extract_cover_letter(page_text, company_name, job_title):
        marker = re.search(r"cover letter(.*?)(?:resume|download|$)", page_text, re.I | re.S)
        if marker and marker.group(1).strip():
            return marker.group(1).strip()
        return (
            f"Dear Hiring Team at {company_name},\n\n"
            f"I am excited to apply for the {job_title} position. My experience and skills "
            "would allow me to contribute immediate value to your team.\n\n"
            "Thank you for your consideration.\n\nSincerely,\nCandidate"
        )

    @staticmethod
    def _parse_resume_for_export(page_text, company_name, job_title):
        lines = [line.strip() for line in page_text.splitlines() if line.strip()]
        return {
            "name": lines[0] if lines else "Applicant",
            "summary": f"Tailored professional profile for {job_title} at {company_name}.",
            "experiences": [{
                "title": job_title, "company": company_name, "dates": "Recent",
                "bullets": lines[1:5] or ["Delivered high-impact results in a collaborative environment."]
            }],
            "skills": ["Leadership", "Project Management", "Technical Execution", "Strategic Planning"],
            "education": [{"degree": "Bachelor's Degree", "school": "Accredited Institution"}],
        }

    @classmethod
    def delete_account_by_id(cls, run_id):
        logs = AccountLogger.get_logs()
        target = next((item for item in logs if item.get("id") == run_id), None)
        if not target or not target.get("email") or not target.get("password"):
            return {"success": False, "error": "Account credentials were not found"}
        engine = cls()
        try:
            with engine._browser() as page:
                engine._login(page, target["email"], target["password"])
                page.goto(f"{SWOOPED_URL}/app/settings", wait_until="domcontentloaded")
                engine._click_first(page, ["delete account", "close account", "delete"], timeout=10000)
                engine._click_first(page, ["confirm", "delete account", "yes"], timeout=10000)
            AccountLogger.add_or_update_log(run_id, status="Deleted on Swooped", deleted=True)
            return {"success": True, "message": "Account successfully deleted from Swooped.co"}
        except Exception as exc:
            AccountLogger.add_or_update_log(run_id, status=f"Delete Failed: {exc}")
            return {"success": False, "error": str(exc)}
