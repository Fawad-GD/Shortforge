FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    STORAGE_PATH=/data/storage CLIPIFY_DIR=/opt/clipify

# fonts-noto-core gives captions Arabic / Urdu / Devanagari glyphs; montserrat is the caption face.
RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg git curl fonts-dejavu-core fonts-montserrat fonts-noto-core libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# The open-source processing engine: Clipify (MIT), pinned for reproducible builds.
ARG CLIPIFY_REF=995e7611b9d97209009fe086b639c53c9a5007e5
RUN git clone https://github.com/Siraj-zaki/clipify /opt/clipify \
    && cd /opt/clipify && git checkout "$CLIPIFY_REF" && rm -rf .git

WORKDIR /srv
COPY requirements.txt .
RUN pip install -r /opt/clipify/requirements.txt -r requirements.txt

# ShortForge fixes to Clipify (CPU encoder, language detection, safe download, ...).
# The build FAILS if a patch no longer applies, so you never ship an unpatched engine.
COPY patches ./patches
RUN python patches/apply_patches.py /opt/clipify

COPY adapter ./adapter
COPY tests ./tests
RUN mkdir -p /data/storage

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://localhost:8000/health || exit 1
CMD ["uvicorn", "adapter.main:app", "--host", "0.0.0.0", "--port", "8000"]
