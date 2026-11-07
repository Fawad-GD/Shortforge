import { useQueryClient } from "@tanstack/react-query";
import { useServerFn } from "@tanstack/react-start";
import { useEffect } from "react";

import { syncJobs } from "@/lib/worker.functions";

/** While jobs are running, pull real progress from the processing server every few seconds. */
export function useJobSync(enabled: boolean, projectId?: string) {
  const sync = useServerFn(syncJobs);
  const qc = useQueryClient();
  useEffect(() => {
    if (!enabled) return;
    let stop = false;
    const tick = async () => {
      try {
        await sync({ data: projectId ? { projectId } : {} });
        qc.invalidateQueries();
      } catch {
        // next tick retries
      }
      if (!stop) timer = setTimeout(tick, 4000);
    };
    let timer = setTimeout(tick, 500);
    return () => {
      stop = true;
      clearTimeout(timer);
    };
  }, [enabled, projectId, sync, qc]);
}
