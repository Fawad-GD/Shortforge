import { StatusBadge } from "@/components/AppShell";
import { formatDuration, formatTimecode, scoreLabel } from "@/lib/format";

export type ShortRow = {
  id: string;
  seq: number;
  title: string | null;
  hook: string | null;
  duration_seconds: number | string | null;
  score: number | string | null;
  start_seconds: number | string;
  end_seconds: number | string;
  render_status: string;
  render_error: string | null;
  thumbnail_path: string | null;
};

export function mediaUrl(shortId: string, token: string | null, kind: "video" | "thumbnail" = "video", download = false) {
  if (!token) return "";
  return `/api/media/${shortId}?kind=${kind}&t=${encodeURIComponent(token)}${download ? "&dl=1" : ""}`;
}

export function ShortCard({
  short, token, selected, onSelect, onOpen,
}: { short: ShortRow; token: string | null; selected: boolean; onSelect: (v: boolean) => void; onOpen: () => void }) {
  return (
    <div className="panel overflow-hidden">
      <button type="button" onClick={onOpen} className="relative block aspect-[9/16] w-full bg-muted" aria-label={`Open ${short.title ?? "clip"}`}>
        {short.thumbnail_path && token ? (
          <img src={mediaUrl(short.id, token, "thumbnail")} alt="" className="h-full w-full object-cover" loading="lazy" />
        ) : (
          <span className="absolute inset-0 grid place-items-center text-xs text-muted-foreground capitalize">{short.render_status}</span>
        )}
        <span className="absolute bottom-2 right-2 rounded bg-background/80 px-1.5 py-0.5 font-mono text-[11px]">
          {formatDuration(Number(short.duration_seconds))}
        </span>
      </button>
      <div className="space-y-1.5 p-3">
        <div className="flex items-start gap-2">
          <input type="checkbox" checked={selected} onChange={(e) => onSelect(e.target.checked)} aria-label="Select clip" className="mt-1 accent-primary" />
          <p className="line-clamp-2 text-sm font-medium">{short.title ?? `Short ${short.seq}`}</p>
        </div>
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>Score {scoreLabel(Number(short.score))}</span>
          <span className="font-mono">{formatTimecode(Number(short.start_seconds))}</span>
        </div>
        {short.render_status !== "completed" && <StatusBadge status={short.render_status} />}
        {short.render_error && <p className="text-xs text-destructive">{short.render_error}</p>}
      </div>
    </div>
  );
}
