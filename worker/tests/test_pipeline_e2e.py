"""Real end-to-end test: FFmpeg + the patched Clipify scripts + validation + ZIP.

Download and Whisper are pre-seeded (they need the internet / a model download),
everything after transcription is the genuine production code path.
"""
import json
import random
import shutil
import subprocess
import uuid
import zipfile

import pytest

from adapter import engine
from conftest import HAVE_CLIPIFY

pytestmark = pytest.mark.skipif(not (HAVE_CLIPIFY and shutil.which("ffmpeg")),
                                reason="needs ffmpeg and a Clipify checkout")


def _seed_project(duration=100):
    uid, pid = str(uuid.uuid4()), str(uuid.uuid4())
    wd = engine.project_dir(uid, pid)
    ff = ["ffmpeg", "-y", "-loglevel", "error"]
    subprocess.run([*ff, "-f", "lavfi", "-i", f"testsrc2=size=1280x720:rate=25:duration={duration}",
                    "-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
                    str(wd / "source.mp4")], check=True)
    subprocess.run([*ff, "-i", str(wd / "source.mp4"), "-vn", "-ac", "1", "-ar", "16000",
                    str(wd / "audio.wav")], check=True)
    rnd = random.Random(7)
    vocab = "honestly nobody actually knows the secret reason why people never finish".split()
    segs, t = [], 0.0
    for sid in range(200):
        if t > duration - 3:
            break
        words, st = [], t
        for i in range(12):
            w = rnd.choice(vocab) + ("." if i == 11 else "")
            words.append({"start": round(t, 3), "end": round(t + 0.38, 3), "word": " " + w})
            t += 0.4
        segs.append({"id": sid, "start": st, "end": round(t, 3),
                     "text": " ".join(x["word"].strip() for x in words), "words": words})
    (wd / "transcript.json").write_text(json.dumps({"duration": duration, "segments": segs}))
    return uid, pid, wd


def test_full_pipeline_renders_valid_shorts_and_zip():
    from adapter.main import app
    from fastapi.testclient import TestClient

    uid, pid, wd = _seed_project()
    with TestClient(app):  # starts the worker threads exactly as in production
        job = engine.create_job({"project_id": pid, "user_id": uid, "max_clips": 2})
        done = engine.wait_for(job["id"], 600)

    assert done["status"] == "completed", done.get("error")
    assert done["progress"] == 100
    shorts = done["shorts"]
    assert 1 <= len(shorts) <= 2
    for s in shorts:
        assert s["render_status"] == "completed" and s["validated"] is True
        assert (s["width"], s["height"]) == (1080, 1920)
        assert 20 <= s["duration_seconds"] <= 62
        out = engine.absolute(s["output_path"])
        assert out.is_file() and out.stat().st_size > 10_000
        info = engine._probe(out)
        assert info["video_codec"] == "h264" and info["has_audio"]
        assert engine.absolute(s["thumbnail_path"]).is_file()
        assert engine.servable(s["output_path"]) and engine.servable(s["thumbnail_path"])
    # clips are unique moments: no two overlap in the source video
    spans = sorted((s["start_seconds"], s["end_seconds"]) for s in shorts)
    assert all(a_end <= b_start for (_, a_end), (b_start, _) in zip(spans, spans[1:]))

    z = engine.build_zip(uid, pid)
    with zipfile.ZipFile(engine.absolute(z["path"])) as archive:
        assert archive.testzip() is None and len(archive.namelist()) == len(shorts)
    assert engine.servable(z["path"])


def test_voice_is_not_pitch_shifted():
    """A 440 Hz tone must stay 440 Hz (the original engine shifted it by 3%)."""
    import numpy as np

    uid, pid, wd = _seed_project(duration=70)
    from adapter.main import app
    from fastapi.testclient import TestClient

    with TestClient(app):
        done = engine.wait_for(engine.create_job({"project_id": pid, "user_id": uid, "max_clips": 1})["id"], 600)
    assert done["status"] == "completed", done.get("error")
    out = engine.absolute(done["shorts"][0]["output_path"])
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(out), "-t", "5", "-ac", "1",
                          "-ar", "16000", "-f", "s16le", "-"], capture_output=True, check=True).stdout
    samples = np.frombuffer(raw, dtype=np.int16).astype(float)
    spectrum = np.abs(np.fft.rfft(samples * np.hanning(len(samples))))
    peak_hz = np.argmax(spectrum) * 16000 / len(samples)
    assert abs(peak_hz - 440) < 3, peak_hz
