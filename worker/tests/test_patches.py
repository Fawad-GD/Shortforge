import shutil
from pathlib import Path

import pytest

import apply_patches
from conftest import HAVE_CLIPIFY

pytestmark = pytest.mark.skipif(not HAVE_CLIPIFY, reason="Clipify checkout not available")


def _scripts():
    import os
    return Path(os.environ["CLIPIFY_DIR"]) / "scripts"


def test_all_patches_present_and_idempotent():
    root = _scripts().parent
    assert all(line.startswith("already applied") for line in apply_patches.apply(root))


def test_patched_behaviour():
    s = _scripts()
    assert 'language="en"' not in (s / "transcribe.py").read_text()
    render = (s / "render.py").read_text()
    assert "rubberband" not in render and 'VOICE_FILTER = "anull"' in render
    dl = (s / "download.py").read_text()
    assert '"--",\n        url' in dl and "--no-playlist" in dl


def test_patch_fails_loudly_when_clipify_changes(tmp_path):
    fake = tmp_path / "clipify"
    shutil.copytree(_scripts(), fake / "scripts")
    (fake / "scripts" / "render.py").write_text("# totally different file\n")
    with pytest.raises(SystemExit, match="PATCH FAILED"):
        apply_patches.apply(fake)
