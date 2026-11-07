import uuid

import pytest
from fastapi.testclient import TestClient

from adapter import engine, main
from adapter.main import app
from adapter.storage import RemoteStore
from conftest import AUTH, FakeClient

H = AUTH


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _renders_dir():
    uid, pid = str(uuid.uuid4()), str(uuid.uuid4())
    return uid, pid, engine.project_dir(uid, pid) / "renders"


def test_health_public_and_token_check(client):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/health", headers=H).json()["authenticated"] is True
    assert client.get("/health", headers={"Authorization": "Bearer nope"}).status_code == 401


def test_protected_routes_need_token(client):
    assert client.post("/process", json={"url": "https://x.y/z"}).status_code == 401
    assert client.get("/jobs/00000000-0000-0000-0000-000000000000/status", headers=H).status_code == 404
    assert client.get("/api/files", params={"path": "../../etc/passwd"}, headers=H).status_code == 400


@pytest.mark.parametrize("url", [
    "--exec=touch /tmp/pwned", "file:///etc/passwd", "http://169.254.169.254/",
    "http://127.0.0.1:8000/health", "https://user:pw@example.com/v"])
def test_process_rejects_unsafe_urls(client, url):
    r = client.post("/api/process", json={"url": url}, headers=H)
    assert r.status_code == 422, r.text


def test_project_url_cannot_smuggle_options(client):
    uid, pid = str(uuid.uuid4()), str(uuid.uuid4())
    r = client.post("/api/process", json={"project_id": pid, "user_id": uid,
                                          "url": "--exec=rm -rf /"}, headers=H)
    assert r.status_code == 422


def test_validate_url_rejects_internal(client):
    r = client.post("/api/validate-url", json={"url": "http://169.254.169.254/latest"}, headers=H)
    assert r.status_code == 422 and "private" in r.json()["detail"]


def test_files_only_serves_finished_outputs(client):
    uid, pid, renders = _renders_dir()
    base = renders.parent
    (renders / "short_01.mp4").write_bytes(b"0123456789" * 100)
    (renders / "short_01.jpg").write_bytes(b"jpg")
    (renders / "shorts.zip").write_bytes(b"zip")
    (base / "source.mp4").write_bytes(b"private source")
    (base / "transcript.json").write_text("{}")
    rel = f"users/{uid}/projects/{pid}"
    for ok in ("short_01.mp4", "short_01.jpg", "shorts.zip"):
        assert client.get("/api/files", params={"path": f"{rel}/renders/{ok}"}, headers=H).status_code == 200
    for blocked in (f"{rel}/source.mp4", f"{rel}/transcript.json", f"{rel}/logs/render_1.log",
                    f"{rel}/renders/../source.mp4", "jobs/anything.json"):
        r = client.get("/api/files", params={"path": blocked}, headers=H)
        assert r.status_code in (400, 403), (blocked, r.status_code)
    assert client.get("/api/files", params={"path": f"{rel}/renders/short_09.mp4"}, headers=H).status_code == 404


def test_video_seeking_works_via_range_requests(client):
    uid, pid, renders = _renders_dir()
    (renders / "short_01.mp4").write_bytes(bytes(range(256)) * 8)
    path = f"users/{uid}/projects/{pid}/renders/short_01.mp4"
    r = client.get("/api/files", params={"path": path}, headers={**H, "Range": "bytes=10-19"})
    assert r.status_code == 206
    assert r.content == bytes(range(10, 20))
    assert r.headers["content-range"].startswith("bytes 10-19/")


def test_missing_local_file_is_restored_from_gcs(client, monkeypatch):
    fake = FakeClient()
    store = RemoteStore(bucket="b", client=fake)
    monkeypatch.setattr(main, "remote", store)
    uid, pid = str(uuid.uuid4()), str(uuid.uuid4())
    rel = f"users/{uid}/projects/{pid}/renders/short_01.mp4"
    fake.store[rel] = b"FROM-THE-BUCKET"
    r = client.get("/api/files", params={"path": rel}, headers=H)
    assert r.status_code == 200 and r.content == b"FROM-THE-BUCKET"
    assert engine.absolute(rel).is_file()  # cached locally afterwards
    assert client.get("/api/files", params={"path": rel.replace("01", "02")}, headers=H).status_code == 404


def test_delete_project_removes_local_and_bucket_files(client, monkeypatch):
    fake = FakeClient()
    store = RemoteStore(bucket="b", client=fake)
    monkeypatch.setattr(engine, "remote", store)
    uid, pid, renders = _renders_dir()
    (renders / "short_01.mp4").write_bytes(b"v")
    fake.store[f"users/{uid}/projects/{pid}/renders/short_01.mp4"] = b"v"
    fake.store["users/other/projects/x/renders/short_01.mp4"] = b"keep"
    assert client.delete(f"/api/projects/{pid}", params={"user_id": uid}, headers=H).json() == {"deleted": True}
    assert not renders.exists()
    assert list(fake.store) == ["users/other/projects/x/renders/short_01.mp4"]


def test_system_status_reports_real_state(client):
    body = client.get("/api/system/status", headers=H).json()
    assert body["backend"] is True and body["ffmpeg"] is True
    assert body["encoder"] in ("libx264", "h264_nvenc")
    assert body["storage"]["backend"] == "local disk"


def test_cpu_host_never_selects_gpu_encoder(monkeypatch):
    monkeypatch.delenv("CLIPIFY_ENCODER", raising=False)
    monkeypatch.setattr(engine, "gpu_available", lambda: False)
    assert engine.encoder_name() == "libx264"
    monkeypatch.setattr(engine, "gpu_available", lambda: True)
    assert engine.encoder_name() == "h264_nvenc"
