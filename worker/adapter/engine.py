"""Thin adapter around the open-source Clipify pipeline (MIT).

Clipify (https://github.com/Siraj-zaki/clipify) does the real work:
  scripts/download.py      yt-dlp -> source.mp4 + 16 kHz audio.wav
  scripts/transcribe.py    faster-whisper, word-level timestamps
  scripts/curate_llm.py    highlight detection (Ollama/Claude/OpenAI, falls back to
                           the free regex/heuristic curator scripts/curate.py)
  scripts/speaker_track.py YuNet face tracking -> 9:16 crop curve
  scripts/make_ass.py      word-highlighted captions from real word times
  scripts/render.py        FFmpeg render with burned-in captions

This module only orders those steps, records real progress, and normalises
each output to H.264/AAC MP4 at the requested 9:16 size.
"""

from __future__ import annotations

import json
import os
import queue
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .netguard import check_public_video_url
from .storage import remote

CLIPIFY_DIR = Path(os.environ.get("CLIPIFY_DIR", "/opt/clipify")).resolve()
SCRIPTS = CLIPIFY_DIR / "scripts"
STORAGE = Path(os.environ.get("STORAGE_PATH", "/data/storage")).resolve()
JOBS_DIR = STORAGE / "jobs"
FFMPEG = os.environ.get("FFMPEG_BIN", "ffmpeg")
FFPROBE = os.environ.get("FFPROBE_BIN", "ffprobe")
PY = sys.executable
CONCURRENCY = max(1, int(os.environ.get("WORKER_CONCURRENCY", "1")))
DEFAULT_MAX_CLIPS = int(os.environ.get("MAX_CLIPS", "40"))
TOP_N = int(os.environ.get("CLIPIFY_TOP_N", "40"))
WHISPER_MODEL = os.environ.get("CLIPIFY_WHISPER_MODEL", "small")
STEP_TIMEOUT = int(os.environ.get("STEP_TIMEOUT_SECONDS", str(3 * 3600)))

def gpu_available() -> bool:
    """True only if an NVIDIA GPU is really usable (not just that ffmpeg lists nvenc)."""
    if not shutil.which("nvidia-smi"):
        return False
    try:
        return subprocess.run(["nvidia-smi", "-L"], capture_output=True, timeout=10).returncode == 0
    except Exception:
        return False


def encoder_name() -> str:
    """CPU encoder unless a GPU is verifiably present. Override: CLIPIFY_ENCODER."""
    return os.environ.get("CLIPIFY_ENCODER") or ("h264_nvenc" if gpu_available() else "libx264")


STAGES = {
    "queued": ("Queued", 0),
    "downloading": ("Downloading", 5),
    "transcribing": ("Transcribing", 20),
    "analyzing": ("Analyzing", 50),
    "selecting": ("Selecting clips", 55),
    "rendering": ("Rendering", 60),
    "finalizing": ("Finalizing", 97),
    "completed": ("Completed", 100),
    "failed": ("Failed", None),
    "cancelled": ("Cancelled", None),
}

_UUID = re.compile(r"^[0-9a-fA-F-]{36}$")
_lock = threading.Lock()
_jobs: dict[str, dict[str, Any]] = {}
_procs: dict[str, subprocess.Popen] = {}
_queue: "queue.Queue[str]" = queue.Queue()


class StepError(RuntimeError):
    pass


class Cancelled(RuntimeError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def check_id(value: str | None) -> str:
    if not value or not _UUID.match(value):
        raise ValueError("invalid identifier")
    return value


def engine_ready() -> bool:
    return (SCRIPTS / "render.py").exists() and shutil.which(FFMPEG) is not None


# ---------------------------------------------------------------- paths


def workdir_for(job: dict[str, Any]) -> Path:
    if job.get("user_id") and job.get("project_id"):
        return project_dir(job["user_id"], job["project_id"])
    path = STORAGE / "jobs" / check_id(job["id"]) / "work"
    path.mkdir(parents=True, exist_ok=True)
    return path


def project_dir(user_id: str, project_id: str) -> Path:
    path = (STORAGE / "users" / check_id(user_id) / "projects" / check_id(project_id)).resolve()
    for sub in ("clips", "renders", "logs"):
        (path / sub).mkdir(parents=True, exist_ok=True)
    return path


def relative(path: Path) -> str:
    return str(Path(path).resolve().relative_to(STORAGE))


_SERVABLE = re.compile(
    r"^users/[0-9a-fA-F-]{36}/projects/[0-9a-fA-F-]{36}/renders/"
    r"(short_\d{2,3}\.(mp4|jpg)|shorts\.zip)$")


def servable(rel: str) -> bool:
    """Only finished clips, thumbnails and the ZIP may leave the server — never the
    source video, transcripts, job files or logs, whatever path a client asks for."""
    return bool(_SERVABLE.match(rel))


def absolute(rel: str) -> Path:
    path = (STORAGE / rel).resolve()
    if not str(path).startswith(str(STORAGE) + os.sep):
        raise ValueError("path traversal detected")
    return path


# ----------------------------------------------------------------- jobs


def _save(job: dict[str, Any]) -> None:
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    job["updated_at"] = now()
    tmp = JOBS_DIR / f"{job['id']}.json.tmp"
    tmp.write_text(json.dumps(job, indent=1))
    tmp.replace(JOBS_DIR / f"{job['id']}.json")


def get_job(job_id: str) -> dict[str, Any] | None:
    with _lock:
        job = _jobs.get(job_id)
        return json.loads(json.dumps(job)) if job else None


def _set(job_id: str, **fields: Any) -> None:
    with _lock:
        job = _jobs[job_id]
        if job["status"] == "cancelled" and fields.get("status") not in (None, "cancelled"):
            return
        stage = fields.get("stage")
        if stage:
            label, pct = STAGES.get(stage, (stage, None))
            job["stage_label"] = label
            if pct is not None and "progress" not in fields:
                fields["progress"] = pct
        job.update(fields)
        _save(job)


def _log(job_id: str, message: str) -> None:
    with _lock:
        job = _jobs[job_id]
        job.setdefault("logs", []).append({"t": now(), "m": message[:500]})
        job["logs"] = job["logs"][-60:]
        _save(job)


def create_job(payload: dict[str, Any]) -> dict[str, Any]:
    job_id = payload.get("job_id") or str(uuid.uuid4())
    check_id(job_id)
    for key in ("project_id", "user_id"):
        if payload.get(key):
            check_id(payload[key])
    if payload.get("url"):
        payload = {**payload, "url": check_public_video_url(payload["url"])}
    with _lock:
        if job_id in _jobs and _jobs[job_id]["status"] in ("queued", "processing"):
            return json.loads(json.dumps(_jobs[job_id]))
    job = {
        "id": job_id,
        "kind": payload.get("kind", "pipeline"),
        "project_id": payload.get("project_id"),
        "user_id": payload.get("user_id"),
        "url": payload.get("url"),
        "options": {
            "max_clips": int(payload.get("max_clips") or DEFAULT_MAX_CLIPS),
            "resolution": payload.get("resolution") or "1080x1920",
            "rank": payload.get("rank"),
            "seq": payload.get("seq"),
        },
        "status": "queued",
        "stage": "queued",
        "stage_label": "Queued",
        "progress": 0,
        "error": None,
        "shorts": [],
        "logs": [],
        "engine": "clipify",
        "created_at": now(),
        "started_at": None,
        "completed_at": None,
    }
    with _lock:
        _jobs[job_id] = job
        _save(job)
    _queue.put(job_id)
    return json.loads(json.dumps(job))


def cancel_job(job_id: str) -> bool:
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            return False
        if job["status"] in ("queued", "processing"):
            job.update(status="cancelled", stage="cancelled", stage_label="Cancelled",
                       completed_at=now())
            _save(job)
        proc = _procs.get(job_id)
    if proc and proc.poll() is None:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass
    return True


def queue_length() -> int:
    return _queue.qsize()


# ------------------------------------------------------------ subprocess


def _run(job_id: str, cmd: list[str], label: str, wd: Path, env: dict[str, str] | None = None,
         cwd: Path | None = None) -> None:
    job = get_job(job_id)
    if not job or job["status"] == "cancelled":
        raise Cancelled()
    log_path = wd / "logs" / f"{label}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    full_env = {**os.environ, "CLIPIFY_WORK": str(wd), "CLIPIFY_OUTPUT": str(wd / "clips"),
                "CLIPIFY_WHISPER_MODEL": WHISPER_MODEL, "PYTHONUNBUFFERED": "1",
                "CLIPIFY_ENCODER": encoder_name(), "CLIPIFY_TOP_N": str(TOP_N),
                "CLIPIFY_LANGUAGE": os.environ.get("CLIPIFY_LANGUAGE", ""), **(env or {})}
    with log_path.open("w") as log:
        proc = subprocess.Popen(cmd, cwd=str(cwd or SCRIPTS), env=full_env, stdout=log,
                                stderr=subprocess.STDOUT, start_new_session=True)
        with _lock:
            _procs[job_id] = proc
        try:
            code = proc.wait(timeout=STEP_TIMEOUT)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            raise StepError(f"{label} took too long and was stopped.")
        finally:
            with _lock:
                _procs.pop(job_id, None)
    job = get_job(job_id)
    if job and job["status"] == "cancelled":
        raise Cancelled()
    if code != 0:
        tail = log_path.read_text(errors="replace").strip().splitlines()[-12:]
        raise StepError(f"{label} failed: " + " | ".join(tail)[-700:])


def _probe(path: Path) -> dict[str, Any]:
    out = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries",
         "format=duration,size:stream=codec_type,codec_name,width,height",
         "-of", "json", str(path)], capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise StepError("The file could not be read as a video.")
    data = json.loads(out.stdout or "{}")
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    fmt = data.get("format", {})
    return {
        "duration": float(fmt.get("duration") or 0),
        "size_bytes": int(fmt.get("size") or path.stat().st_size),
        "width": video.get("width"), "height": video.get("height"),
        "video_codec": video.get("codec_name"),
        "audio_codec": audio.get("codec_name") if audio else None,
        "has_audio": audio is not None,
    }


# --------------------------------------------------------------- pipeline


def _prepare_source(job_id: str, job: dict[str, Any], wd: Path) -> None:
    src = wd / "source.mp4"
    if not src.exists():
        if not job.get("url"):
            raise StepError("No video was uploaded or linked for this project.")
        _set(job_id, stage="downloading")
        _log(job_id, "Downloading with yt-dlp")
        _run(job_id, [PY, str(SCRIPTS / "download.py"), job["url"]], "download", wd)
        if not src.exists():
            raise StepError("The video could not be downloaded. It may be private, "
                            "age-restricted or blocked for download.")
    if not (wd / "audio.wav").exists():
        _run(job_id, [FFMPEG, "-y", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000",
                      str(wd / "audio.wav")], "audio", wd, cwd=wd)


def _transcribe(job_id: str, wd: Path) -> None:
    if (wd / "transcript.json").exists():
        _log(job_id, "Reusing cached transcript")
        return
    _set(job_id, stage="transcribing")
    _log(job_id, f"Transcribing with faster-whisper ({WHISPER_MODEL})")
    _run(job_id, [PY, str(SCRIPTS / "transcribe.py")], "transcribe", wd)
    data = json.loads((wd / "transcript.json").read_text())
    words = data if isinstance(data, list) else data.get("words") or data.get("segments") or []
    if not words:
        raise StepError("No speech was detected in this video, so no clips could be chosen.")


def _curate(job_id: str, wd: Path) -> list[dict[str, Any]]:
    _set(job_id, stage="analyzing")
    _set(job_id, stage="selecting")
    try:
        _run(job_id, [PY, str(SCRIPTS / "curate_llm.py")], "curate", wd)
    except StepError as exc:
        _log(job_id, f"AI curator unavailable, using free heuristic curator ({exc})"[:300])
        _run(job_id, [PY, str(SCRIPTS / "curate.py")], "curate", wd)
    cands = json.loads((wd / "candidates.json").read_text())
    return sorted(cands, key=lambda c: c.get("rank", 999))


def _render_one(job_id: str, wd: Path, cand: dict[str, Any], seq: int, resolution: str) -> dict[str, Any]:
    rank = int(cand["rank"])
    (wd / "selected_clip.json").write_text(json.dumps(cand))
    _run(job_id, [PY, str(SCRIPTS / "speaker_track.py"), str(wd / "source.mp4"),
                  str(cand["start"]), str(cand["end"]), str(wd / "track.json")], f"track_{rank}", wd)
    _run(job_id, [PY, str(SCRIPTS / "make_ass.py")], f"captions_{rank}", wd)
    for old in (wd / "clips").glob(f"clip{rank:02d}_*.mp4"):
        old.unlink()
    _run(job_id, [PY, str(SCRIPTS / "render.py"), str(rank)], f"render_{rank}", wd)
    produced = sorted((wd / "clips").glob(f"clip{rank:02d}_*.mp4"), key=lambda p: p.stat().st_mtime)
    if not produced:
        raise StepError("Clipify finished without writing a clip file.")

    w, h = (int(x) for x in resolution.split("x"))
    out = wd / "renders" / f"short_{seq:02d}.mp4"
    _run(job_id, [FFMPEG, "-y", "-i", str(produced[-1]),
                  "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease:flags=lanczos,"
                         f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1",
                  "-c:v", "libx264", "-preset", os.environ.get("X264_PRESET", "veryfast"),
                  "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                  "-movflags", "+faststart", str(out)], f"finalize_{rank}", wd, cwd=wd)
    info = _probe(out)
    if info["video_codec"] != "h264" or not info["has_audio"] or info["duration"] < 1:
        raise StepError("The rendered clip failed the quality check.")
    thumb = wd / "renders" / f"short_{seq:02d}.jpg"
    subprocess.run([FFMPEG, "-y", "-ss", f"{info['duration'] / 2:.2f}", "-i", str(out),
                    "-frames:v", "1", "-vf", "scale=540:-2", str(thumb)],
                   capture_output=True, timeout=120)
    remote.upload(out, relative(out))
    if thumb.exists():
        remote.upload(thumb, relative(thumb))
    return {
        "output_path": relative(out),
        "thumbnail_path": relative(thumb) if thumb.exists() else None,
        "width": info["width"], "height": info["height"],
        "file_size_bytes": info["size_bytes"], "duration_seconds": info["duration"],
        "render_status": "completed", "validated": True, "render_error": None,
    }


def _short_meta(cand: dict[str, Any], seq: int) -> dict[str, Any]:
    return {
        "seq": seq, "rank": cand.get("rank"), "title": cand.get("title"),
        "hook": cand.get("hook") or cand.get("title"),
        "transcript_text": cand.get("text"),
        "start_seconds": cand.get("start"), "end_seconds": cand.get("end"),
        "score": cand.get("virality"),
        "score_breakdown": {k: cand.get(k) for k in
                            ("virality", "raw_score", "hook_hits", "story_starter", "density_wps")
                            if k in cand},
        "explanation": cand.get("reason") or cand.get("why"),
    }


def _pipeline(job_id: str) -> None:
    job = get_job(job_id)
    assert job
    wd = workdir_for(job)
    resolution = job["options"]["resolution"]
    _prepare_source(job_id, job, wd)
    _transcribe(job_id, wd)
    cands = _curate(job_id, wd)[: job["options"]["max_clips"]]
    if not cands:
        raise StepError("No strong standalone moments were found in this video.")
    _log(job_id, f"Selected {len(cands)} clips")
    _set(job_id, stage="rendering", shorts=[{**_short_meta(c, i + 1), "render_status": "queued"}
                                            for i, c in enumerate(cands)])
    ok = 0
    for i, cand in enumerate(cands):
        seq = i + 1
        try:
            result = _render_one(job_id, wd, cand, seq, resolution)
            ok += 1
        except Cancelled:
            raise
        except Exception as exc:  # one bad clip never sinks the whole job
            result = {"render_status": "failed", "render_error": str(exc)[:500], "validated": False}
            _log(job_id, f"Clip {seq} failed: {exc}"[:400])
        with _lock:
            _jobs[job_id]["shorts"][i].update(result)
        _set(job_id, stage="rendering", progress=round(60 + 37 * (i + 1) / len(cands), 1))
    _set(job_id, stage="finalizing")
    if ok == 0:
        raise StepError("Every clip failed to render. See the job log for details.")


def _rerender(job_id: str) -> None:
    job = get_job(job_id)
    assert job
    wd = workdir_for(job)
    rank, seq = job["options"].get("rank"), job["options"].get("seq") or 1
    cands = json.loads((wd / "candidates.json").read_text())
    cand = next((c for c in cands if c.get("rank") == rank), None)
    if not cand:
        raise StepError("That clip is no longer in the candidate list.")
    _set(job_id, stage="rendering")
    result = _render_one(job_id, wd, cand, int(seq), job["options"]["resolution"])
    _set(job_id, shorts=[{**_short_meta(cand, int(seq)), **result}], stage="finalizing")


def _worker_loop() -> None:
    while True:
        job_id = _queue.get()
        job = get_job(job_id)
        if not job or job["status"] != "queued":
            continue
        _set(job_id, status="processing", started_at=now())
        try:
            (_rerender if job["kind"] == "render" else _pipeline)(job_id)
            _set(job_id, status="completed", stage="completed", completed_at=now())
        except Cancelled:
            _set(job_id, status="cancelled", stage="cancelled", completed_at=now())
        except Exception as exc:
            _set(job_id, status="failed", stage="failed", error=str(exc)[:800], completed_at=now())


def start() -> None:
    """Load persisted jobs and resume anything interrupted by a restart."""
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(JOBS_DIR.glob("*.json")):
        try:
            job = json.loads(path.read_text())
        except Exception:
            continue
        _jobs[job["id"]] = job
        if job["status"] in ("queued", "processing"):
            job["status"] = "queued"  # cached steps are skipped, so this resumes
            _queue.put(job["id"])
    for _ in range(CONCURRENCY):
        threading.Thread(target=_worker_loop, daemon=True).start()


# ---------------------------------------------------------------- helpers


def save_upload_as_source(wd: Path, temp: Path) -> dict[str, Any]:
    """Normalise an upload to source.mp4 and drop any stale cached analysis."""
    info = _probe(temp)
    if not info["width"]:
        raise StepError("That file has no video track.")
    dst = wd / "source.mp4"
    for stale in ("source.mp4", "audio.wav", "transcript.json", "candidates.json"):
        (wd / stale).unlink(missing_ok=True)
    copy = subprocess.run([FFMPEG, "-y", "-i", str(temp), "-c", "copy", "-movflags", "+faststart",
                           str(dst)], capture_output=True, timeout=3600)
    if copy.returncode != 0:
        subprocess.run([FFMPEG, "-y", "-i", str(temp), "-c:v", "libx264", "-preset", "veryfast",
                        "-crf", "20", "-c:a", "aac", str(dst)], capture_output=True, check=True,
                       timeout=6 * 3600)
    temp.unlink(missing_ok=True)
    return {**info, "storage_path": relative(dst)}


def build_zip(user_id: str, project_id: str) -> dict[str, Any]:
    wd = project_dir(user_id, project_id)
    files = sorted((wd / "renders").glob("short_*.mp4"))
    if not files:
        raise StepError("There are no finished clips to download yet.")
    zip_path = wd / "renders" / "shorts.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as archive:
        for f in files:
            archive.write(f, arcname=f.name)
    remote.upload(zip_path, relative(zip_path))
    return {"path": relative(zip_path), "count": len(files), "size_bytes": zip_path.stat().st_size}


def delete_project(user_id: str, project_id: str) -> None:
    shutil.rmtree(STORAGE / "users" / check_id(user_id) / "projects" / check_id(project_id),
                  ignore_errors=True)
    remote.delete_prefix(f"users/{user_id}/projects/{project_id}/")


def validate_url(url: str) -> dict[str, Any]:
    url = check_public_video_url(url)
    out = subprocess.run([PY, "-m", "yt_dlp", "--dump-single-json", "--no-download",
                          "--no-playlist", "--no-warnings", "--", url],
                         capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        msg = (out.stderr or "").strip().splitlines()[-1:] or ["Unknown error"]
        raise StepError("We couldn't open that video: " + msg[0].replace("ERROR: ", "")[:300])
    data = json.loads(out.stdout)
    if data.get("is_live"):
        raise StepError("Live streams can't be processed. Wait until the stream has ended.")
    return {"title": data.get("title"), "duration": data.get("duration"),
            "thumbnail": data.get("thumbnail"), "extractor": data.get("extractor_key")}


def wait_for(job_id: str, timeout: float) -> dict[str, Any] | None:
    end = time.time() + timeout
    while time.time() < end:
        job = get_job(job_id)
        if job and job["status"] not in ("queued", "processing"):
            return job
        time.sleep(1)
    return get_job(job_id)
