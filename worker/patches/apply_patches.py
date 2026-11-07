"""Apply ShortForge's fixes to the pinned Clipify checkout.

Run at image build time:  python patches/apply_patches.py /opt/clipify
Every patch asserts that the text it replaces exists, so if Clipify is ever
bumped to a version that changed these lines the BUILD FAILS LOUDLY instead of
silently shipping an unpatched engine. Re-running is safe (idempotent).

Why each patch exists
---------------------
encoder    Clipify picks h264_nvenc/vaapi/qsv whenever ffmpeg merely *lists* the
           encoder. Stock Debian/Ubuntu ffmpeg lists them even with no GPU, so on
           a CPU-only host every render failed ("Cannot load libcuda.so.1").
           We honour CLIPIFY_ENCODER=libx264 and give it sane intermediate flags.
language   transcribe.py forced language="en". We auto-detect (or use
           CLIPIFY_LANGUAGE) so Urdu / Arabic / Spanish / French work.
voice      render.py pitch-shifted the speaker's voice 3% so the audio would
           differ from the original ("voice signature"). That is a way of evading
           audio fingerprinting, which ShortForge does not do. Audio is now left
           untouched.
download   Put "--" before the URL (a URL beginning with "-" could otherwise be
           parsed by yt-dlp as an option) and refuse playlists.
top_n      Clipify capped candidates at 25. Configurable now (CLIPIFY_TOP_N).
"""

from __future__ import annotations

import sys
from pathlib import Path

PATCHES: list[tuple[str, str, str, str]] = [
    ("encoder", "config.py",
     "    if override and has(override):\n        return override, []\n",
     "    if override and has(override):\n"
     "        if override == \"libx264\":\n"
     "            # Intermediate file: ShortForge re-encodes it at the final size.\n"
     "            return override, [\"-preset\", \"veryfast\", \"-crf\", \"16\"]\n"
     "        return override, []\n"),
    ("language", "transcribe.py",
     "    language=\"en\",\n",
     "    language=(os.environ.get(\"CLIPIFY_LANGUAGE\") or None),\n"),
    ("voice", "render.py",
     "VOICE_FILTER = \"rubberband=pitch=1.03,equalizer=f=6000:t=q:w=1:g=2,volume=1.0\"",
     "VOICE_FILTER = \"anull\"  # ShortForge: audio is never altered"),
    ("download", "download.py",
     "        url,\n    ]",
     "        \"--no-playlist\",\n        \"--\",\n        url,\n    ]"),
    ("top_n", "curate.py",
     "import json, re, sys\n",
     "import json, os, re, sys\n"),
    ("top_n", "curate.py",
     "    if len(picked) >= 25:",
     "    if len(picked) >= int(os.environ.get(\"CLIPIFY_TOP_N\", \"40\")):"),
    ("top_n", "curate_llm.py",
     "TOP_N = 25\n",
     "TOP_N = int(os.environ.get(\"CLIPIFY_TOP_N\", \"40\"))\n"),
]


def apply(clipify_dir: Path) -> list[str]:
    scripts = clipify_dir / "scripts"
    report: list[str] = []
    for name, filename, old, new in PATCHES:
        path = scripts / filename
        text = path.read_text()
        if new in text:
            report.append(f"already applied: {name} ({filename})")
            continue
        if old not in text:
            raise SystemExit(
                f"PATCH FAILED: '{name}' could not find its target in {filename}. "
                "Clipify changed; review patches/apply_patches.py before building."
            )
        path.write_text(text.replace(old, new, 1))
        report.append(f"applied: {name} ({filename})")
    return report


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "/opt/clipify")
    for line in apply(target):
        print(line)
