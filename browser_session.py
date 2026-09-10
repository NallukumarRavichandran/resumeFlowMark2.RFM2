import os
import tempfile
import time
import uuid

from remote_browser_engine import RemoteBrowserError, RemoteBrowserSwoopedEngine


_sessions = {}


def _client():
    return RemoteBrowserSwoopedEngine._client()


def _live_view_url(client, run):
    events = client.runs.events(run.id, limit=100)
    for event in events.events:
        if event.type == "browser.ready":
            return event.data.get("live_view_url")
    return None


def _wait_for_live_browser(client, run, timeout=45):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        url = _live_view_url(client, run)
        if url:
            return url
        time.sleep(1)
    raise RemoteBrowserError("Remote browser did not become available within 45 seconds.")


def start_session(message, resume_file=None):
    with _client() as client:
        workspace = client.workspaces.create(name=f"resumeflow-ui-{uuid.uuid4().hex[:8]}")
        attachment_note = ""
        if resume_file:
            suffix = os.path.splitext(resume_file.filename or "resume.pdf")[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
                temp.write(resume_file.content)
                temp_path = temp.name
            try:
                client.workspaces.upload(workspace.id, temp_path)
            finally:
                os.unlink(temp_path)
            attachment_note = " The uploaded resume is available in the workspace."

        run = client.runs.create(
            f"Open https://swooped.co in the live browser. Do not use APIs. "
            f"Open the page, report the current URL, and finish this task immediately. "
            f"Do not wait, sign in, or perform any other action; the user will control "
            f"the browser through follow-up commands. "
            f"User request: {message}{attachment_note}",
            workspace_id=workspace.id,
        )
        live_view_url = _wait_for_live_browser(client, run)
        client.runs.wait_for_completion(run.id, timeout=90)
        session_id = str(run.session_id)
        _sessions[session_id] = {
            "workspace_id": str(workspace.id),
            "last_run_id": str(run.id),
            "live_view_url": live_view_url,
        }
        return {
            "session_id": session_id,
            "run_id": str(run.id),
            "workspace_id": str(workspace.id),
            "live_view_url": live_view_url,
            "message": "Remote browser session started.",
        }


def send_message(session_id, message):
    state = _sessions.get(session_id)
    if not state:
        raise RemoteBrowserError("This remote browser session is not available in this server process.")
    with _client() as client:
        run = client.runs.create(message, session_id=session_id)
        result = client.runs.wait_for_completion(run.id)
        state["last_run_id"] = str(run.id)
        refreshed_url = _live_view_url(client, run)
        if refreshed_url:
            state["live_view_url"] = refreshed_url
        return {
            "session_id": session_id,
            "run_id": str(run.id),
            "live_view_url": state["live_view_url"],
            "result": getattr(result, "result", str(result)),
        }
