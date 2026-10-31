import os
import json
import secrets
import asyncio
import subprocess
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from swooped_engine import SwoopedEngine, DOWNLOADS_DIR, PREVIEWS_DIR
from account_logger import AccountLogger
from browser_session import start_session, send_message

app = FastAPI(title="ResumeFlow Mark 2 - Swooped.co Automation", version="2.0.0")

# ---------------------------------------------------------------------------
# Configuration (environment-driven)
# ---------------------------------------------------------------------------
# Optional shared secret protecting the dashboard and every /api/* route.
# Unset => no auth (local development default).
DASHBOARD_TOKEN = os.environ.get("DASHBOARD_TOKEN", "").strip()
AUTH_COOKIE_NAME = "rfm2_token"

# Comma-separated list of browser origins allowed to call the API cross-site.
# The dashboard itself is same-origin, so this only matters for external tools.
# Wildcard "*" is accepted but then credentials are disallowed (per CORS spec).
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "ALLOWED_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000"
    ).split(",")
    if origin.strip()
]

# /api/open-folder shells out to xdg-open / os.startfile. Useless (and risky)
# on a headless server, so it is opt-in.
ENABLE_OPEN_FOLDER = os.environ.get("ENABLE_OPEN_FOLDER", "").strip().lower() in {
    "1", "true", "yes", "on"
}


def _token_matches(candidate):
    """Constant-time comparison; always False when DASHBOARD_TOKEN is unset
    callers must gate on DASHBOARD_TOKEN being configured first."""
    if not candidate:
        return False
    return secrets.compare_digest(
        str(candidate).encode("utf-8"), DASHBOARD_TOKEN.encode("utf-8")
    )


def _request_authorized(request):
    """True when the request carries a valid dashboard token via
    Authorization: Bearer, the auth cookie, or (for GET /) ?token=."""
    if not DASHBOARD_TOKEN:
        return True
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer ") and _token_matches(auth_header[7:].strip()):
        return True
    if _token_matches(request.cookies.get(AUTH_COOKIE_NAME)):
        return True
    return False


LOGIN_PAGE_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ResumeFlow.ai — Auth Required</title>
<style>
  body{margin:0;min-height:100vh;display:grid;place-items:center;background:#000;color:#fff;
       font-family:Inter,system-ui,sans-serif}
  .card{width:min(360px,90vw);padding:32px;border:1px solid #222;border-radius:16px;background:#0a0a0a}
  h1{font-size:18px;margin:0 0 4px} p{color:#888;font-size:13px;margin:0 0 20px}
  input{width:100%;padding:12px 14px;border-radius:10px;border:1px solid #333;background:#111;
        color:#fff;font-size:14px;box-sizing:border-box}
  button{margin-top:14px;width:100%;padding:12px;border-radius:10px;border:0;background:#fff;
         color:#000;font-weight:600;cursor:pointer}
</style></head><body>
<form class="card" method="post" action="/login">
  <h1>Auth required</h1>
  <p>Enter the dashboard token to continue.</p>
  <input type="password" name="token" placeholder="Dashboard token" autofocus required>
  <button type="submit">Unlock</button>
</form></body></html>"""


@app.middleware("http")
async def dashboard_auth_middleware(request: Request, call_next):
    if not DASHBOARD_TOKEN:
        return await call_next(request)
    # CORS preflight must pass through untouched.
    if request.method == "OPTIONS":
        return await call_next(request)
    # POST /login validates the token itself.
    if request.method == "POST" and request.url.path == "/login":
        return await call_next(request)

    authorized = _request_authorized(request)

    # GET /?token=... bootstraps the cookie so the dashboard works in a tab.
    if (
        not authorized
        and request.method == "GET"
        and request.url.path == "/"
        and _token_matches(request.query_params.get("token"))
    ):
        response = await call_next(request)
        response.set_cookie(
            AUTH_COOKIE_NAME,
            request.query_params["token"],
            httponly=True,
            samesite="lax",
            max_age=7 * 24 * 3600,
        )
        return response

    if not authorized:
        if request.url.path == "/":
            return HTMLResponse(LOGIN_PAGE_HTML)
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)

    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials="*" not in ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class BrowserMessage(BaseModel):
    session_id: str
    message: str


@app.post("/api/browser/start")
async def start_browser_session(
    message: str = Form(...),
    resume_file: UploadFile | None = File(None),
):
    resume = None
    if resume_file:
        resume = type("ResumeUpload", (), {
            "filename": resume_file.filename,
            "content": await resume_file.read(),
        })()
    try:
        return start_session(message, resume)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/browser/message")
async def continue_browser_session(payload: BrowserMessage):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    try:
        return send_message(payload.session_id, payload.message)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

@app.get("/", response_class=HTMLResponse)
async def read_root():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>ResumeFlow Mark 2 Backend Running</h1>")


@app.post("/login")
async def login(request: Request):
    form = await request.form()
    candidate = str(form.get("token", "") or "")
    if DASHBOARD_TOKEN and _token_matches(candidate):
        response = RedirectResponse("/", status_code=303)
        response.set_cookie(
            AUTH_COOKIE_NAME,
            candidate,
            httponly=True,
            samesite="lax",
            max_age=7 * 24 * 3600,
        )
        return response
    return HTMLResponse(LOGIN_PAGE_HTML, status_code=401)


def _safe_file_path(base_dir, *parts):
    """Join user-supplied path segments under base_dir and reject traversal.

    Each segment must be a plain filename (no separators, no ".."). The
    resolved path must remain inside base_dir after symlink resolution.
    """
    for part in parts:
        if (
            not part
            or part in {".", ".."}
            or "/" in part
            or "\\" in part
            or os.path.basename(part) != part
        ):
            raise HTTPException(status_code=400, detail="Invalid path")
    base = os.path.realpath(base_dir)
    target = os.path.realpath(os.path.join(base, *parts))
    if os.path.commonpath([base, target]) != base:
        raise HTTPException(status_code=400, detail="Invalid path")
    return target


@app.get("/api/logs")
async def get_logs():
    return AccountLogger.get_logs(redact=True)


@app.get("/api/browser-preview/{filename}")
async def browser_preview(filename: str):
    preview_path = _safe_file_path(PREVIEWS_DIR, filename)
    if not os.path.exists(preview_path):
        raise HTTPException(status_code=404, detail="Browser preview not found")
    return FileResponse(preview_path, media_type="image/png", headers={"Cache-Control": "no-store"})

@app.post("/api/generate")
async def generate_documents(
    resume_file: UploadFile = File(...),
    company_name: str = Form(...),
    job_title: str = Form(...),
    job_description: str = Form(...)
):
    resume_bytes = await resume_file.read()
    filename = resume_file.filename or "resume.pdf"

    async def event_generator():
        queue = asyncio.Queue()

        def progress_callback(step, total, message, data=None):
            event = {
                "step": step,
                "total": total,
                "message": message,
                "data": data
            }
            queue.put_nowait(event)

        engine = SwoopedEngine(progress_callback=progress_callback)

        # Run pipeline in a worker thread so asyncio remains non-blocking
        loop = asyncio.get_event_loop()
        task = loop.run_in_executor(
            None,
            engine.execute_pipeline,
            resume_bytes,
            filename,
            company_name,
            job_title,
            job_description
        )

        while True:
            # Check if there are queued events
            while not queue.empty():
                evt = queue.get_nowait()
                yield f"data: {json.dumps(evt)}\n\n"

            if task.done():
                try:
                    res = task.result()
                    if isinstance(res, dict):
                        # Never ship account credentials to the browser.
                        res = {k: v for k, v in res.items() if k != "password"}
                    final_evt = {
                        "step": 6,
                        "total": 6,
                        "done": True,
                        "message": "Completed! Documents generated & credentials ready.",
                        "result": res
                    }
                    yield f"data: {json.dumps(final_evt)}\n\n"
                except Exception as e:
                    err_evt = {
                        "error": True,
                        "message": str(e)
                    }
                    yield f"data: {json.dumps(err_evt)}\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/download/{folder_name}/{filename}")
async def download_file(folder_name: str, filename: str):
    file_path = _safe_file_path(DOWNLOADS_DIR, folder_name, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    media_type = "application/pdf" if filename.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return FileResponse(file_path, filename=filename, media_type=media_type)

@app.post("/api/open-folder")
async def open_local_folder(folder_name: str = Form(...)):
    if not ENABLE_OPEN_FOLDER:
        raise HTTPException(
            status_code=403,
            detail="Folder opening is disabled on this deployment. "
                   "Set ENABLE_OPEN_FOLDER=true to enable it.",
        )
    safe_folder = os.path.basename(folder_name)
    target_path = _safe_file_path(DOWNLOADS_DIR, safe_folder)
    if not os.path.exists(target_path):
        target_path = os.path.realpath(DOWNLOADS_DIR)
        
    try:
        if os.name == 'nt':
            os.startfile(target_path)
        else:
            subprocess.Popen(["xdg-open", target_path])
        return {"success": True, "path": target_path}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/delete-account")
async def delete_swooped_account(account_id: str = Form(...)):
    result = SwoopedEngine.delete_account_by_id(account_id)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
