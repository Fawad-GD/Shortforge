import { useServerFn } from "@tanstack/react-start";
import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { mediaUrl } from "@/components/ShortCard";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { supabase } from "@/integrations/supabase/client";
import { formatDuration, formatTimecode, scoreLabel } from "@/lib/format";
import { rerenderShort } from "@/lib/worker.functions";

type Short = {
  id: string; seq: number; title: string | null; hook: string | null; explanation: string | null;
  start_seconds: number | string; end_seconds: number | string; duration_seconds: number | string | null;
  score: number | string | null; render_status: string; output_path: string | null;
  caption_settings: Record<string, unknown> | null; captions_enabled: boolean;
  score_breakdown: Record<string, number> | null;
};

export function ShortDialog({ short, sourceDuration, token, onClose }: {
  short: Short | null; sourceDuration: number; token: string | null; onClose: () => void;
}) {
  const qc = useQueryClient();
  const rerender = useServerFn(rerenderShort);
  const [title, setTitle] = useState("");
  const [start, setStart] = useState(0);
  const [end, setEnd] = useState(0);
  const [captionStyle, setCaptionStyle] = useState("clean");
  const [position, setPosition] = useState("center");
  const [captions, setCaptions] = useState(true);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!short) return;
    setTitle(short.title ?? "");
    setStart(Number(short.start_seconds));
    setEnd(Number(short.end_seconds));
    setCaptionStyle(String(short.caption_settings?.["style"] ?? "clean"));
    setPosition(String(short.caption_settings?.["position"] ?? "center"));
    setCaptions(short.captions_enabled);
  }, [short]);

  if (!short) return null;
  const s0 = Number(short.start_seconds), s1 = Number(short.end_seconds);

  async function save(renderAgain: boolean) {
    if (!short) return;
    if (end - start < 3) { toast.error("A clip must be at least 3 seconds."); return; }
    setBusy(true);
    const { error } = await supabase.from("shorts").update({
      title, start_seconds: start, end_seconds: end, duration_seconds: end - start,
      captions_enabled: captions,
      caption_settings: { ...(short.caption_settings ?? {}), style: captionStyle, position },
    }).eq("id", short.id);
    if (error) { setBusy(false); toast.error(error.message); return; }
    if (renderAgain) {
      const res = await rerender({ data: { shortId: short.id } });
      if (!res.ok) toast.error(res.error); else toast.success("Re-render queued");
    } else toast.success("Saved");
    setBusy(false);
    qc.invalidateQueries();
  }

  async function remove() {
    if (!short || !confirm("Delete this Short?")) return;
    await supabase.from("shorts").delete().eq("id", short.id);
    toast.success("Short deleted");
    qc.invalidateQueries();
    onClose();
  }

  const signals = Object.entries(short.score_breakdown ?? {}).filter(([k]) => !k.endsWith("penalty")).slice(0, 6);

  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-4xl">
        <DialogHeader><DialogTitle>{short.title ?? `Short ${short.seq}`}</DialogTitle></DialogHeader>
        <div className="grid gap-6 md:grid-cols-[280px_1fr]">
          <div className="aspect-[9/16] overflow-hidden rounded-md bg-muted">
            {short.output_path && token ? (
              <video key={short.output_path} src={mediaUrl(short.id, token)} controls className="h-full w-full" />
            ) : <div className="grid h-full place-items-center text-sm capitalize text-muted-foreground">{short.render_status}</div>}
          </div>
          <div className="space-y-4 text-sm">
            {short.hook && <p className="italic text-muted-foreground">“{short.hook}”</p>}
            <div className="flex flex-wrap gap-4 font-mono text-xs">
              <span>{formatDuration(Number(short.duration_seconds))}</span>
              <span>AI Quality Score {scoreLabel(Number(short.score))}</span>
              <span>{formatTimecode(s0)} → {formatTimecode(s1)}</span>
            </div>
            <div aria-label="Position in source video">
              <div className="relative h-2 rounded bg-secondary">
                <div className="absolute h-2 rounded bg-primary" style={{ left: `${(s0 / sourceDuration) * 100}%`, width: `${Math.max(((s1 - s0) / sourceDuration) * 100, 0.5)}%` }} />
              </div>
              <div className="mt-1 flex justify-between font-mono text-[10px] text-muted-foreground"><span>00:00</span><span>{formatDuration(sourceDuration)}</span></div>
            </div>
            {short.explanation && <p className="text-muted-foreground">{short.explanation}</p>}
            {signals.length > 0 && (
              <div className="grid grid-cols-3 gap-2">
                {signals.map(([k, v]) => <div key={k} className="rounded border px-2 py-1 text-xs"><span className="capitalize text-muted-foreground">{k.replace("_", " ")}</span> <span className="font-mono">{Math.round(v * 100)}</span></div>)}
              </div>
            )}
            <div className="grid grid-cols-2 gap-3 border-t pt-4">
              <div className="col-span-2 space-y-1"><Label htmlFor="t">Title</Label><Input id="t" value={title} onChange={(e) => setTitle(e.target.value)} /></div>
              <div className="space-y-1"><Label htmlFor="s">Start (sec)</Label><Input id="s" type="number" step="0.1" min={0} value={start} onChange={(e) => setStart(Number(e.target.value))} /></div>
              <div className="space-y-1"><Label htmlFor="e">End (sec)</Label><Input id="e" type="number" step="0.1" max={sourceDuration} value={end} onChange={(e) => setEnd(Number(e.target.value))} /></div>
              <div className="space-y-1"><Label htmlFor="cs">Caption style</Label>
                <select id="cs" value={captionStyle} onChange={(e) => setCaptionStyle(e.target.value)} className="h-9 w-full rounded-md border border-input bg-background px-2 capitalize">
                  {["clean", "bold", "highlight", "minimal", "dynamic"].map((s) => <option key={s}>{s}</option>)}
                </select></div>
              <div className="space-y-1"><Label htmlFor="cp">Caption position</Label>
                <select id="cp" value={position} onChange={(e) => setPosition(e.target.value)} className="h-9 w-full rounded-md border border-input bg-background px-2">
                  <option value="top">Top</option><option value="center">Center</option><option value="bottom">Bottom</option>
                </select></div>
              <label className="col-span-2 flex items-center gap-2"><input type="checkbox" checked={captions} onChange={(e) => setCaptions(e.target.checked)} className="accent-primary" /> Captions on</label>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button onClick={() => save(true)} disabled={busy}>Save & re-render</Button>
              <Button variant="secondary" onClick={() => save(false)} disabled={busy}>Save</Button>
              {short.output_path && token && <Button variant="outline" asChild><a href={mediaUrl(short.id, token)} download>Download</a></Button>}
              <Button variant="ghost" className="text-destructive" onClick={remove}>Delete</Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
