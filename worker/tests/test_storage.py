from adapter.storage import RemoteStore
from conftest import FakeClient


def test_disabled_store_is_a_noop(tmp_path):
    s = RemoteStore(bucket="")
    f = tmp_path / "a.mp4"; f.write_bytes(b"x")
    assert not s.enabled
    assert s.upload(f, "a.mp4") is False
    assert s.restore("a.mp4", tmp_path / "b") is False
    assert s.delete_prefix("x/") == 0
    assert s.check() == {"backend": "local disk", "ok": True}


def test_upload_restore_delete_roundtrip(tmp_path):
    client = FakeClient()
    s = RemoteStore(bucket="b", client=client)
    f = tmp_path / "short_01.mp4"; f.write_bytes(b"VIDEO")
    assert s.upload(f, "users/u/projects/p/renders/short_01.mp4") is True
    restored = tmp_path / "deep" / "dir" / "copy.mp4"
    assert s.restore("users/u/projects/p/renders/short_01.mp4", restored) is True
    assert restored.read_bytes() == b"VIDEO"
    assert not list(restored.parent.glob("*.part"))
    assert s.restore("users/u/projects/p/renders/missing.mp4", tmp_path / "m") is False
    s.upload(f, "users/u/projects/p/renders/short_02.mp4")
    s.upload(f, "users/u/projects/OTHER/renders/short_01.mp4")
    assert s.delete_prefix("users/u/projects/p/") == 2
    assert list(client.store) == ["users/u/projects/OTHER/renders/short_01.mp4"]


def test_upload_failure_never_raises(tmp_path):
    s = RemoteStore(bucket="b", client=FakeClient(fail=True))
    f = tmp_path / "x.mp4"; f.write_bytes(b"x")
    assert s.upload(f, "x.mp4") is False
    assert "PermissionError" in s.last_error


def test_check_reports_ok():
    assert RemoteStore(bucket="b", client=FakeClient()).check()["ok"] is True
