# ShortForge processing server

The video engine behind the website. The website (Supabase login + database + UI) sends jobs here;
this server downloads/ingests the video, transcribes it, finds standalone moments, crops them to
9:16 with face tracking, burns in word-synced captions, renders with FFmpeg, validates each file and
serves it back. Engine: [Clipify](https://github.com/Siraj-zaki/clipify) (MIT) + the adapter in `adapter/`.

```
Browser ─▶ Website (login, DB, UI) ──Bearer token──▶ this server ──▶ Google Cloud Storage (copies of finished Shorts)
```

## What is fixed compared with stock Clipify (all covered by tests)
| Problem in the original | Fix |
|---|---|
| Every render failed on CPU-only machines (it picked the `h264_nvenc` GPU encoder just because FFmpeg lists it) | CPU encoder unless a GPU is verified |
| Transcription forced to English | Language auto-detected (or `CLIPIFY_LANGUAGE`) |
| Speaker's voice was pitch-shifted 3% to change its "voice signature" (a fingerprint-evasion trick) | Removed — audio is never altered |
| A project's `source_url` was passed to yt-dlp unchecked (option injection / internal-network access) | Strict URL validation, `--` separator, private/internal addresses blocked |
| `/api/files` served any file in storage | Only finished clips, thumbnails and the ZIP |
| Max 25 moments per video | Up to `CLIPIFY_TOP_N` (default 40), non-overlapping |
| Files lost if the disk was lost | Copied to Google Cloud Storage and restored on demand |

## Choose where to run it

**Important — YouTube links and cloud servers.** YouTube commonly blocks downloads from data-centre IPs
(including Google Cloud) with "Sign in to confirm you're not a bot". Workarounds (residential proxies, cookie
tricks) circumvent YouTube's access controls, so they are deliberately **not** included. Therefore:

| | Home PC / home server (Option A) | Google Cloud VM (Option B) |
|---|---|---|
| Uploaded video files | ✅ | ✅ |
| YouTube/other links | ✅ usually works (residential IP) | ⚠️ often blocked by YouTube |
| Cost | $0 | Not free: needs ≥2 vCPU/8 GB. Covered by the $300 / 90-day new-account credit, then ~US$50/month |
| Always on | Only while your PC is on | Yes |
| Google Cloud Storage | Optional | Built in |

The free `e2-micro` VM (1 GB RAM) is too small for Whisper + FFmpeg except for tiny experiments.
Cloud Run is **not** suitable: this worker keeps jobs in memory and on disk and needs CPU between requests.

### Option A — your own machine ($0)
```bash
cd worker
cp .env.example .env            # set SHORTFORGE_ACCESS_TOKEN=$(openssl rand -hex 32)
docker compose --profile tunnel up --build -d
docker compose logs tunnel      # copy the https://xxxx.trycloudflare.com address
```
`WORKER_URL` = that address. (A quick-tunnel address changes on restart; a free named Cloudflare tunnel keeps it fixed.)

### Option B — Google Cloud
1. Create a project with billing enabled (new accounts get free credits) and open **Cloud Shell**.
2. Upload this `worker/` folder (or clone your repo) and run:
   ```bash
   bash deploy/gcp/setup.sh
   ```
   Optional: `MACHINE_TYPE=e2-standard-4 WHISPER_MODEL=medium RETENTION_DAYS=14 bash deploy/gcp/setup.sh`
3. The script prints your `WORKER_URL` and `SHORTFORGE_ACCESS_TOKEN`. It creates the bucket (outputs auto-delete
   after `RETENTION_DAYS`), a service account limited to that bucket, a static IP, a firewall (ports 80/443 only)
   and the VM with automatic HTTPS.
4. Later: `bash deploy/gcp/update.sh` to ship new code, `bash deploy/gcp/teardown.sh` to delete everything.

### Optional: use Google Cloud Storage from Option A
Create a bucket and a service-account key with *Storage Object Admin* on it, mount the key into the container,
and set `GCS_BUCKET` and `GOOGLE_APPLICATION_CREDENTIALS` in `.env`.

## Connect the website
Add two **server-side** values to wherever the website's backend runs (for Lovable: the project's secrets /
environment settings), then redeploy:
```
WORKER_URL               = https://your-server-address        (no trailing slash)
SHORTFORGE_ACCESS_TOKEN  = the same token as in the worker .env
```
Open **System status** in the site: processing server should read *Online*.
The frontend code is unchanged; nothing is exposed to the browser.

## Configuration (`.env`)
See `.env.example`. Most useful: `CLIPIFY_WHISPER_MODEL` (tiny→large-v3; not `*.en` for non-English),
`CLIPIFY_LANGUAGE`, `MAX_CLIPS`, `CLIPIFY_TOP_N`, `WORKER_CONCURRENCY`, `GCS_BUCKET`, optional AI curator
(`OLLAMA_HOST` / `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`).

## API
All routes need `Authorization: Bearer <token>` except bare `GET /health`. Interactive docs at `/docs`.
`POST /api/process` · `GET /jobs/{id}` · `POST /api/jobs/{id}/cancel` · `POST /api/shorts/render` ·
`POST /api/projects/{id}/upload` · `POST /api/projects/{id}/zip` · `GET /api/files?path=` ·
`DELETE /api/projects/{id}` · `POST /api/validate-url` · `GET /api/system/status`.

## Tests
```bash
docker compose run --rm engine pytest          # in the container
CLIPIFY_DIR=/path/to/clipify pytest            # locally (needs ffmpeg)
```
47 tests: URL/SSRF guard, file allow-list, Range/seek support, GCS upload/restore/delete (against a fake bucket),
patch integrity, and a real end-to-end render (crop, captions, 1080×1920 H.264/AAC, validation, ZIP, audio untouched).

## Limits to know about
- Download and Whisper transcription were not runnable in the build sandbox (no internet to model hosts); they are
  Clipify's own tested stages. Run one real video through your server before relying on it.
- Moment-picking without an AI model uses Clipify's English keyword heuristics plus pace/length; for other
  languages quality is lower. Add Ollama or an API key for better selection.
- Only process videos you own or have permission to use. No DRM/private/paywalled content.
