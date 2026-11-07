"""ShortForge processing server — a thin HTTP adapter over Clipify.

Every endpoint except a bare GET /health requires
  Authorization: Bearer <SHORTFORGE_ACCESS_TOKEN>
The ShortForge web app holds the token as a server-side secret.
"""

from __future__ import annotations

import hmac
import os
import shutil
import uuid
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from . import engine
from .storage import remote

MAX_UPLOAD = int(os.environ.get("MAX_UPLOAD_BYTES", str(5 * 1024**3)))


def _token() -> str:
    return os.environ.get("SHORTFORGE_ACCESS_TOKEN") or os.environ.get("WORKER_API_TOKEN") or ""


@asynccontextmanager
async def lifespan(_: FastAPI):
    if len(_token()) < 16:
        raise RuntimeError("Set SHORTFORGE_ACCESS_TOKEN (16+ chars, e.g. `openssl rand -hex 32`).")
    engine.start()
    yield


app = FastAPI(title="ShortForge processing server (Clipify adapter)", version="2.0.0",
              lifespan=lifespan)


def _valid(authorization: str | None) -> bool:
    supplied = (authorization or "").removeprefix("Bearer ").strip()
    return bool(supplied) and hmac.compare_digest(supplied, _token())


def require_token(authorization: Annotated[str | None, Header()] = None) -> None:
    if not _valid(authorization):
        raise HTTPException(status_code=401, detail="Unauthorized: wrong or missing access token.")


Auth = Depends(require_token)


class ProcessPayload(BaseModel):
    job_id: str | None = None
    url: str | None = Field(default=None, max_length=2000)
    project_id: str | None = None
    user_id: str | None = None
    max_clips: int | None = Field(default=None, ge=1, le=50)
    resolution: str | None = Field(default=None, pattern=r"^\d{3,4}x\d{3,4}$")


class RenderPayload(BaseModel):
    job_id: str | None = None
    project_id: str
    user_id: str
    rank: int
    seq: int
    resolution: str | None = Field(default=None, pattern=r"^\d{3,4}x\d{3,4}$")


class UrlPayload(BaseModel):
    url: str = Field(min_length=8, max_length=2000)


def _status_view(job: dict[str, Any]) -> dict[str, Any]:
    return {k: job.get(k) for k in ("id", "status", "stage", "stage_label", "progress", "error",
                                     "created_at", "started_at", "completed_at", "updated_at")} | {
        "job_id": job["id"],
        "shorts_ready": sum(1 for s in job.get("shorts", []) if s.get("render_status") == "completed"),
        "shorts_total": len(job.get("shorts", [])),
    }


def _job_or_404(job_id: str) -> dict[str, Any]:
    job = engine.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# ------------------------------------------------------------- health


@app.get("/health")
def health(authorization: Annotated[str | None, Header()] = None) -> dict:
    if authorization is not None and not _valid(authorization):
        raise HTTPException(status_code=401, detail="Unauthorized: wrong access token.")
    return {"status": "ok", "engine": "clipify", "engine_ready": engine.engine_ready(),
            "authenticated": authorization is not None, "time": engine.now()}


@app.get("/api/system/status", dependencies=[Auth])
def system_status() -> dict:
    free = shutil.disk_usage(engine.STORAGE).free if engine.STORAGE.exists() else 0
    gpu = engine.gpu_available()
    if os.environ.get("ANTHROPIC_API_KEY"):
        provider = "anthropic"
    elif os.environ.get("OPENAI_API_KEY"):
        provider = "openai"
    elif os.environ.get("OLLAMA_HOST"):
        provider = f"ollama ({os.environ.get('CLIPIFY_OLLAMA_MODEL', 'llama3.1:8b')})"
    else:
        provider = "local heuristic (free)"
    return {
        "backend": True, "engine": "Clipify (MIT, open source)", "engine_ready": engine.engine_ready(),
        "ffmpeg": shutil.which(engine.FFMPEG) is not None,
        "ffprobe": shutil.which(engine.FFPROBE) is not None,
        "whisper_model": engine.WHISPER_MODEL, "gpu": gpu, "storage_free_bytes": free,
        "ai_provider": provider, "ai_configured": True,
        "max_render_workers": engine.CONCURRENCY, "queue_length": engine.queue_length(),
        "encoder": engine.encoder_name(), "storage": remote.check(),
    }


@app.post("/api/validate-url", dependencies=[Auth])
def validate_url(payload: UrlPayload) -> dict:
    try:
        return {"valid": True, **engine.validate_url(payload.url)}
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


# --------------------------------------------------------------- jobs


@app.post("/process", dependencies=[Auth])
@app.post("/api/process", dependencies=[Auth])
def process(payload: ProcessPayload) -> dict:
    if not payload.url and not (payload.project_id and payload.user_id):
        raise HTTPException(status_code=422, detail="Send a video url or a project_id + user_id.")
    try:
        job = engine.create_job(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"job_id": job["id"], "status": job["status"], "job": {"id": job["id"]}}


@app.get("/jobs/{job_id}", dependencies=[Auth])
def job_detail(job_id: str) -> dict:
    return _job_or_404(job_id)


@app.get("/jobs/{job_id}/status", dependencies=[Auth])
def job_status(job_id: str) -> dict:
    return _status_view(_job_or_404(job_id))


@app.get("/shorts/{job_id}", dependencies=[Auth])
def job_shorts(job_id: str) -> dict:
    job = _job_or_404(job_id)
    return {"job_id": job_id, "status": job["status"], "shorts": job.get("shorts", [])}


@app.post("/jobs/{job_id}/cancel", dependencies=[Auth])
@app.post("/api/jobs/{job_id}/cancel", dependencies=[Auth])
def cancel(job_id: str) -> dict:
    if not engine.cancel_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    return {"cancelled": True}


@app.post("/api/shorts/render", dependencies=[Auth])
def rerender(payload: RenderPayload) -> dict:
    try:
        job = engine.create_job({**payload.model_dump(), "kind": "render",
                                 "job_id": payload.job_id or str(uuid.uuid4())})
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"job_id": job["id"], "status": job["status"]}


# -------------------------------------------------------------- files


@app.post("/api/projects/{project_id}/upload", dependencies=[Auth])
async def upload(project_id: str, user_id: Annotated[str, Form()],
                 file: Annotated[UploadFile, File()]) -> dict:
    try:
        wd = engine.project_dir(user_id, project_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    temp = wd / f"upload_{uuid.uuid4().hex}"
    written = 0
    with temp.open("wb") as handle:  # streamed to disk, never held in memory
        while chunk := await file.read(4 * 1024 * 1024):
            written += len(chunk)
            if written > MAX_UPLOAD:
                handle.close()
                temp.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="File exceeds the upload limit.")
            handle.write(chunk)
    try:
        info = engine.save_upload_as_source(wd, temp)
    except Exception as exc:
        temp.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"That file couldn't be read as a video. {exc}"[:400]) from exc
    return {"source_video": {**info, "original_filename": (file.filename or "upload")[:120]}}


@app.post("/api/projects/{project_id}/zip", dependencies=[Auth])
def zip_project(project_id: str, user_id: str) -> dict:
    try:
        return engine.build_zip(user_id, project_id)
    except engine.StepError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/files", dependencies=[Auth])
def get_file(path: str) -> FileResponse:
    try:
        resolved = engine.absolute(path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid path") from exc
    if not engine.servable(engine.relative(resolved)):
        raise HTTPException(status_code=403, detail="That file cannot be downloaded.")
    if not resolved.is_file() and not remote.restore(engine.relative(resolved), resolved):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(resolved, filename=resolved.name)


@app.delete("/api/projects/{project_id}", dependencies=[Auth])
def delete_project(project_id: str, user_id: str) -> dict:
    try:
        engine.delete_project(user_id, project_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"deleted": True}
