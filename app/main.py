"""Prototype document upload API with in-process job tracking."""
from hashlib import sha256
from threading import Lock
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile

app = FastAPI(title="Document Processing Service", version="0.1.0")
jobs: dict[str, dict] = {}
jobs_lock = Lock()
MAX_BYTES = 2 * 1024 * 1024


def process_document(job_id: str, content: bytes) -> None:
    try:
        text = content.decode("utf-8")
        result = {
            "bytes": len(content),
            "words": len(text.split()),
            "sha256": sha256(content).hexdigest(),
        }
        with jobs_lock:
            jobs[job_id] = {"status": "completed", "result": result}
    except Exception as exc:
        with jobs_lock:
            jobs[job_id] = {"status": "failed", "error": str(exc)}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/documents", status_code=202)
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)) -> dict:
    if not file.filename or not file.filename.lower().endswith(".txt"):
        raise HTTPException(status_code=415, detail="Upload a .txt file")
    content = await file.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 2 MiB")
    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=422, detail="File must be UTF-8 text") from None
    job_id = str(uuid4())
    with jobs_lock:
        jobs[job_id] = {"status": "queued"}
    background_tasks.add_task(process_document, job_id, content)
    return {"job_id": job_id, "status": "queued"}


@app.get("/documents/{job_id}")
def get_document(job_id: str) -> dict:
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"job_id": job_id, **job}
