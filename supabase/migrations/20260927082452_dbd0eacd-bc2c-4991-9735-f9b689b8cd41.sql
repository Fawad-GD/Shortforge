
-- profiles
CREATE TABLE public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users ON DELETE CASCADE,
  display_name TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.profiles TO authenticated;
GRANT ALL ON public.profiles TO service_role;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own profile" ON public.profiles FOR ALL TO authenticated USING (auth.uid() = id) WITH CHECK (auth.uid() = id);

CREATE OR REPLACE FUNCTION public.set_updated_at() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path = public AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END; $$;

CREATE OR REPLACE FUNCTION public.handle_new_user() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
  INSERT INTO public.profiles (id, display_name)
  VALUES (NEW.id, COALESCE(NEW.raw_user_meta_data ->> 'display_name', split_part(NEW.email, '@', 1)))
  ON CONFLICT (id) DO NOTHING;
  INSERT INTO public.user_settings (user_id) VALUES (NEW.id) ON CONFLICT (user_id) DO NOTHING;
  RETURN NEW;
END; $$;

-- user settings
CREATE TABLE public.user_settings (
  user_id UUID PRIMARY KEY REFERENCES auth.users ON DELETE CASCADE,
  ai_provider TEXT NOT NULL DEFAULT 'local',
  ai_model TEXT,
  whisper_model TEXT NOT NULL DEFAULT 'base',
  compute_preference TEXT NOT NULL DEFAULT 'auto',
  default_clip_length TEXT NOT NULL DEFAULT 'auto',
  default_quality_mode TEXT NOT NULL DEFAULT 'balanced',
  default_caption_style TEXT NOT NULL DEFAULT 'clean',
  output_resolution TEXT NOT NULL DEFAULT '1080x1920',
  max_concurrent_renders INT NOT NULL DEFAULT 2,
  temp_retention_hours INT NOT NULL DEFAULT 48,
  language TEXT NOT NULL DEFAULT 'auto',
  theme TEXT NOT NULL DEFAULT 'dark',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_settings TO authenticated;
GRANT ALL ON public.user_settings TO service_role;
ALTER TABLE public.user_settings ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own settings" ON public.user_settings FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE TRIGGER on_auth_user_created AFTER INSERT ON auth.users
FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- projects
CREATE TABLE public.projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users ON DELETE CASCADE,
  name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft',
  source_type TEXT NOT NULL DEFAULT 'upload',
  source_url TEXT,
  content_style TEXT NOT NULL DEFAULT 'auto',
  quality_mode TEXT NOT NULL DEFAULT 'balanced',
  clip_count_mode TEXT NOT NULL DEFAULT 'auto',
  clip_count_target INT,
  clip_length_mode TEXT NOT NULL DEFAULT 'auto',
  clip_min_seconds INT NOT NULL DEFAULT 20,
  clip_max_seconds INT NOT NULL DEFAULT 60,
  aspect_ratio TEXT NOT NULL DEFAULT '9:16',
  output_resolution TEXT NOT NULL DEFAULT '1080x1920',
  captions_enabled BOOLEAN NOT NULL DEFAULT true,
  caption_settings JSONB NOT NULL DEFAULT '{"style":"clean","position":"center","maxWordsPerLine":4,"highlightCurrentWord":true}'::jsonb,
  language TEXT NOT NULL DEFAULT 'auto',
  pipeline_version TEXT NOT NULL DEFAULT 'v1',
  stats JSONB NOT NULL DEFAULT '{}'::jsonb,
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX projects_user_idx ON public.projects(user_id, created_at DESC);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.projects TO authenticated;
GRANT ALL ON public.projects TO service_role;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own projects" ON public.projects FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE TRIGGER projects_updated BEFORE UPDATE ON public.projects FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- source videos
CREATE TABLE public.source_videos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES public.projects ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users ON DELETE CASCADE,
  original_filename TEXT,
  storage_path TEXT,
  size_bytes BIGINT,
  duration_seconds NUMERIC,
  width INT,
  height INT,
  fps NUMERIC,
  video_codec TEXT,
  audio_codec TEXT,
  has_audio BOOLEAN,
  rotation INT,
  checksum TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX source_videos_project_idx ON public.source_videos(project_id);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.source_videos TO authenticated;
GRANT ALL ON public.source_videos TO service_role;
ALTER TABLE public.source_videos ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own source videos" ON public.source_videos FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- transcripts
CREATE TABLE public.transcripts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES public.projects ON DELETE CASCADE,
  source_video_id UUID REFERENCES public.source_videos ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users ON DELETE CASCADE,
  language TEXT,
  language_confidence NUMERIC,
  model TEXT,
  full_text TEXT,
  word_count INT,
  has_speech BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX transcripts_project_idx ON public.transcripts(project_id);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.transcripts TO authenticated;
GRANT ALL ON public.transcripts TO service_role;
ALTER TABLE public.transcripts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own transcripts" ON public.transcripts FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE TABLE public.transcript_segments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  transcript_id UUID NOT NULL REFERENCES public.transcripts ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users ON DELETE CASCADE,
  idx INT NOT NULL,
  kind TEXT NOT NULL DEFAULT 'sentence',
  text TEXT NOT NULL,
  start_seconds NUMERIC NOT NULL,
  end_seconds NUMERIC NOT NULL,
  confidence NUMERIC,
  words JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX transcript_segments_transcript_idx ON public.transcript_segments(transcript_id, idx);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.transcript_segments TO authenticated;
GRANT ALL ON public.transcript_segments TO service_role;
ALTER TABLE public.transcript_segments ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own segments" ON public.transcript_segments FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- clip candidates
CREATE TABLE public.clip_candidates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES public.projects ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users ON DELETE CASCADE,
  start_seconds NUMERIC NOT NULL,
  end_seconds NUMERIC NOT NULL,
  transcript_text TEXT,
  score NUMERIC,
  score_breakdown JSONB NOT NULL DEFAULT '{}'::jsonb,
  selected BOOLEAN NOT NULL DEFAULT false,
  rejected_reason TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX clip_candidates_project_idx ON public.clip_candidates(project_id, score DESC);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.clip_candidates TO authenticated;
GRANT ALL ON public.clip_candidates TO service_role;
ALTER TABLE public.clip_candidates ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own candidates" ON public.clip_candidates FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- shorts
CREATE TABLE public.shorts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES public.projects ON DELETE CASCADE,
  source_video_id UUID REFERENCES public.source_videos ON DELETE SET NULL,
  candidate_id UUID REFERENCES public.clip_candidates ON DELETE SET NULL,
  user_id UUID NOT NULL REFERENCES auth.users ON DELETE CASCADE,
  seq INT NOT NULL DEFAULT 1,
  title TEXT,
  hook TEXT,
  description TEXT,
  hashtags TEXT[],
  transcript_text TEXT,
  start_seconds NUMERIC NOT NULL,
  end_seconds NUMERIC NOT NULL,
  duration_seconds NUMERIC,
  score NUMERIC,
  score_breakdown JSONB NOT NULL DEFAULT '{}'::jsonb,
  explanation TEXT,
  category TEXT,
  language TEXT,
  captions_enabled BOOLEAN NOT NULL DEFAULT true,
  caption_settings JSONB NOT NULL DEFAULT '{}'::jsonb,
  crop_settings JSONB NOT NULL DEFAULT '{}'::jsonb,
  render_status TEXT NOT NULL DEFAULT 'pending',
  render_error TEXT,
  output_path TEXT,
  thumbnail_path TEXT,
  output_width INT,
  output_height INT,
  file_size_bytes BIGINT,
  validated BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX shorts_project_idx ON public.shorts(project_id, seq);
CREATE INDEX shorts_user_idx ON public.shorts(user_id, created_at DESC);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.shorts TO authenticated;
GRANT ALL ON public.shorts TO service_role;
ALTER TABLE public.shorts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own shorts" ON public.shorts FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE TRIGGER shorts_updated BEFORE UPDATE ON public.shorts FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- processing jobs
CREATE TABLE public.processing_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES public.projects ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users ON DELETE CASCADE,
  short_id UUID REFERENCES public.shorts ON DELETE CASCADE,
  kind TEXT NOT NULL DEFAULT 'pipeline',
  stage TEXT NOT NULL DEFAULT 'queued',
  stage_label TEXT,
  progress NUMERIC NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'queued',
  worker_task_id TEXT,
  error_message TEXT,
  retry_count INT NOT NULL DEFAULT 0,
  logs JSONB NOT NULL DEFAULT '[]'::jsonb,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX processing_jobs_project_idx ON public.processing_jobs(project_id, created_at DESC);
CREATE INDEX processing_jobs_status_idx ON public.processing_jobs(status);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.processing_jobs TO authenticated;
GRANT ALL ON public.processing_jobs TO service_role;
ALTER TABLE public.processing_jobs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own jobs" ON public.processing_jobs FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE TRIGGER jobs_updated BEFORE UPDATE ON public.processing_jobs FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

ALTER PUBLICATION supabase_realtime ADD TABLE public.processing_jobs;
ALTER PUBLICATION supabase_realtime ADD TABLE public.shorts;
ALTER PUBLICATION supabase_realtime ADD TABLE public.projects;
