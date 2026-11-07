import { queryOptions } from "@tanstack/react-query";

import { supabase } from "@/integrations/supabase/client";

export const projectsQuery = queryOptions({
  queryKey: ["projects"],
  queryFn: async () => {
    const { data, error } = await supabase
      .from("projects")
      .select("*, shorts(count), clip_candidates(count)")
      .order("created_at", { ascending: false });
    if (error) throw error;
    return data;
  },
});

export const dashboardQuery = queryOptions({
  queryKey: ["dashboard"],
  queryFn: async () => {
    const [projects, shorts, jobs, sources, recentShorts] = await Promise.all([
      supabase.from("projects").select("id", { count: "exact", head: true }),
      supabase.from("shorts").select("id", { count: "exact", head: true }).eq("render_status", "completed"),
      supabase.from("processing_jobs").select("id", { count: "exact", head: true }).in("status", ["queued", "processing"]),
      supabase.from("source_videos").select("size_bytes"),
      supabase.from("shorts").select("id,title,duration_seconds,score,render_status,project_id,created_at")
        .order("created_at", { ascending: false }).limit(6),
    ]);
    const completedProjects = await supabase.from("projects").select("id", { count: "exact", head: true }).eq("status", "completed");
    return {
      projects: projects.count ?? 0,
      processed: completedProjects.count ?? 0,
      shorts: shorts.count ?? 0,
      processing: jobs.count ?? 0,
      storageBytes: (sources.data ?? []).reduce((sum, r) => sum + Number(r.size_bytes ?? 0), 0),
      recentShorts: recentShorts.data ?? [],
    };
  },
});

export const projectQuery = (id: string) =>
  queryOptions({
    queryKey: ["project", id],
    queryFn: async () => {
      const [project, source, jobs, shorts] = await Promise.all([
        supabase.from("projects").select("*").eq("id", id).maybeSingle(),
        supabase.from("source_videos").select("*").eq("project_id", id).order("created_at", { ascending: false }).limit(1).maybeSingle(),
        supabase.from("processing_jobs").select("*").eq("project_id", id).order("created_at", { ascending: false }).limit(5),
        supabase.from("shorts").select("*").eq("project_id", id).order("seq"),
      ]);
      if (project.error) throw project.error;
      return { project: project.data, source: source.data, jobs: jobs.data ?? [], shorts: shorts.data ?? [] };
    },
  });

export const jobsQuery = queryOptions({
  queryKey: ["jobs"],
  queryFn: async () => {
    const { data, error } = await supabase
      .from("processing_jobs")
      .select("*, projects(name)")
      .order("created_at", { ascending: false })
      .limit(50);
    if (error) throw error;
    return data;
  },
});

export const allShortsQuery = queryOptions({
  queryKey: ["shorts"],
  queryFn: async () => {
    const { data, error } = await supabase
      .from("shorts")
      .select("*, projects(name)")
      .order("created_at", { ascending: false });
    if (error) throw error;
    return data;
  },
});
