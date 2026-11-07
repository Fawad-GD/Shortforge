<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.
<!-- LOVABLE:END -->

## Architecture
- Heavy video work (FFmpeg, Whisper, Celery) lives in `worker/` as a self-hosted Python server; the web app only calls it via `src/lib/worker.server.ts` using WORKER_URL + WORKER_API_TOKEN secrets — Workers runtime can't run FFmpeg.
- Media/upload/ZIP streaming goes through `src/routes/api/*` routes that verify the Supabase token and project ownership before proxying to the worker.
- The worker writes job progress straight to the database; the UI reads it via realtime, so progress is never simulated.
