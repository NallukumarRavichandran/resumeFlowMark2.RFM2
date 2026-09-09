import os
import json
import asyncio
import subprocess
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from swooped_engine import SwoopedEngine, DOWNLOADS_DIR
from account_logger import AccountLogger

app = FastAPI(title="ResumeFlow Mark 2 - Swooped.co Automation", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>ResumeFlow Mark 2 Backend Running</h1>")

@app.get("/api/logs")
async def get_logs():
    return AccountLogger.get_logs()

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
                    final_evt = {
                        "step": 6,
                        "total": 6,
                        "done": True,
                        "message": "Completed! Documents ready & account wiped on Swooped.",
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
    file_path = os.path.join(DOWNLOADS_DIR, folder_name, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    media_type = "application/pdf" if filename.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return FileResponse(file_path, filename=filename, media_type=media_type)

@app.post("/api/open-folder")
async def open_local_folder(folder_name: str = Form(...)):
    target_path = os.path.join(DOWNLOADS_DIR, folder_name)
    if not os.path.exists(target_path):
        target_path = DOWNLOADS_DIR
        
    try:
        if os.name == 'nt':
            os.startfile(target_path)
        else:
            subprocess.Popen(["xdg-open", target_path])
        return {"success": True, "path": target_path}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
