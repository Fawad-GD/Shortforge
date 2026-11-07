"""Test setup: isolated storage + a *patched* private copy of Clipify.

Environment is configured before any adapter module is imported, because
adapter.engine reads it at import time.
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "patches"))

_TMP = Path(tempfile.mkdtemp(prefix="shortforge-tests-"))
TOKEN = "test-token-1234567890"
os.environ["SHORTFORGE_ACCESS_TOKEN"] = TOKEN
os.environ["STORAGE_PATH"] = str(_TMP / "storage")
os.environ.pop("GCS_BUCKET", None)

_SRC = Path(os.environ.get("CLIPIFY_DIR", "/opt/clipify"))
HAVE_CLIPIFY = (_SRC / "scripts" / "render.py").exists()
if HAVE_CLIPIFY:
    import apply_patches  # noqa: E402

    _DST = _TMP / "clipify"
    shutil.copytree(_SRC, _DST, ignore=shutil.ignore_patterns(".git", "web", "node_modules"))
    apply_patches.apply(_DST)
    os.environ["CLIPIFY_DIR"] = str(_DST)

AUTH = {"Authorization": f"Bearer {TOKEN}"}


@pytest.fixture(scope="session")
def tmp_root() -> Path:
    return _TMP


class FakeBlob:
    def __init__(self, store: dict, name: str, fail: bool = False):
        self.store, self.name, self.fail = store, name, fail

    def upload_from_filename(self, path: str) -> None:
        if self.fail:
            raise PermissionError("403 forbidden")
        self.store[self.name] = Path(path).read_bytes()

    def exists(self) -> bool:
        return self.name in self.store

    def download_to_filename(self, path: str) -> None:
        Path(path).write_bytes(self.store[self.name])

    def delete(self) -> None:
        del self.store[self.name]


class FakeBucket:
    def __init__(self, store: dict, fail: bool = False):
        self.store, self.fail = store, fail

    def blob(self, name: str) -> FakeBlob:
        return FakeBlob(self.store, name, self.fail)

    def list_blobs(self, prefix: str = ""):
        return [FakeBlob(self.store, n) for n in list(self.store) if n.startswith(prefix)]

    def exists(self) -> bool:
        return True


class FakeClient:
    def __init__(self, fail: bool = False):
        self.store: dict[str, bytes] = {}
        self.fail = fail

    def bucket(self, _name: str) -> FakeBucket:
        return FakeBucket(self.store, self.fail)
