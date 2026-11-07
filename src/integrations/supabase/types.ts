export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "14.17"
  }
  public: {
    Tables: {
      clip_candidates: {
        Row: {
          created_at: string
          end_seconds: number
          id: string
          project_id: string
          rejected_reason: string | null
          score: number | null
          score_breakdown: Json
          selected: boolean
          start_seconds: number
          transcript_text: string | null
          user_id: string
        }
        Insert: {
          created_at?: string
          end_seconds: number
          id?: string
          project_id: string
          rejected_reason?: string | null
          score?: number | null
          score_breakdown?: Json
          selected?: boolean
          start_seconds: number
          transcript_text?: string | null
          user_id: string
        }
        Update: {
          created_at?: string
          end_seconds?: number
          id?: string
          project_id?: string
          rejected_reason?: string | null
          score?: number | null
          score_breakdown?: Json
          selected?: boolean
          start_seconds?: number
          transcript_text?: string | null
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "clip_candidates_project_id_fkey"
            columns: ["project_id"]
            isOneToOne: false
            referencedRelation: "projects"
            referencedColumns: ["id"]
          },
        ]
      }
      processing_jobs: {
        Row: {
          completed_at: string | null
          created_at: string
          error_message: string | null
          id: string
          kind: string
          logs: Json
          progress: number
          project_id: string
          retry_count: number
          short_id: string | null
          stage: string
          stage_label: string | null
          started_at: string | null
          status: string
          updated_at: string
          user_id: string
          worker_task_id: string | null
        }
        Insert: {
          completed_at?: string | null
          created_at?: string
          error_message?: string | null
          id?: string
          kind?: string
          logs?: Json
          progress?: number
          project_id: string
          retry_count?: number
          short_id?: string | null
          stage?: string
          stage_label?: string | null
          started_at?: string | null
          status?: string
          updated_at?: string
          user_id: string
          worker_task_id?: string | null
        }
        Update: {
          completed_at?: string | null
          created_at?: string
          error_message?: string | null
          id?: string
          kind?: string
          logs?: Json
          progress?: number
          project_id?: string
          retry_count?: number
          short_id?: string | null
          stage?: string
          stage_label?: string | null
          started_at?: string | null
          status?: string
          updated_at?: string
          user_id?: string
          worker_task_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "processing_jobs_project_id_fkey"
            columns: ["project_id"]
            isOneToOne: false
            referencedRelation: "projects"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "processing_jobs_short_id_fkey"
            columns: ["short_id"]
            isOneToOne: false
            referencedRelation: "shorts"
            referencedColumns: ["id"]
          },
        ]
      }
      profiles: {
        Row: {
          created_at: string
          display_name: string | null
          id: string
          updated_at: string
        }
        Insert: {
          created_at?: string
          display_name?: string | null
          id: string
          updated_at?: string
        }
        Update: {
          created_at?: string
          display_name?: string | null
          id?: string
          updated_at?: string
        }
        Relationships: []
      }
      projects: {
        Row: {
          aspect_ratio: string
          caption_settings: Json
          captions_enabled: boolean
          clip_count_mode: string
          clip_count_target: number | null
          clip_length_mode: string
          clip_max_seconds: number
          clip_min_seconds: number
          content_style: string
          created_at: string
          error_message: string | null
          id: string
          language: string
          name: string
          output_resolution: string
          pipeline_version: string
          quality_mode: string
          source_type: string
          source_url: string | null
          stats: Json
          status: string
          updated_at: string
          user_id: string
        }
        Insert: {
          aspect_ratio?: string
          caption_settings?: Json
          captions_enabled?: boolean
          clip_count_mode?: string
          clip_count_target?: number | null
          clip_length_mode?: string
          clip_max_seconds?: number
          clip_min_seconds?: number
          content_style?: string
          created_at?: string
          error_message?: string | null
          id?: string
          language?: string
          name: string
          output_resolution?: string
          pipeline_version?: string
          quality_mode?: string
          source_type?: string
          source_url?: string | null
          stats?: Json
          status?: string
          updated_at?: string
          user_id: string
        }
        Update: {
          aspect_ratio?: string
          caption_settings?: Json
          captions_enabled?: boolean
          clip_count_mode?: string
          clip_count_target?: number | null
          clip_length_mode?: string
          clip_max_seconds?: number
          clip_min_seconds?: number
          content_style?: string
          created_at?: string
          error_message?: string | null
          id?: string
          language?: string
          name?: string
          output_resolution?: string
          pipeline_version?: string
          quality_mode?: string
          source_type?: string
          source_url?: string | null
          stats?: Json
          status?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: []
      }
      shorts: {
        Row: {
          candidate_id: string | null
          caption_settings: Json
          captions_enabled: boolean
          category: string | null
          created_at: string
          crop_settings: Json
          description: string | null
          duration_seconds: number | null
          end_seconds: number
          explanation: string | null
          file_size_bytes: number | null
          hashtags: string[] | null
          hook: string | null
          id: string
          language: string | null
          output_height: number | null
          output_path: string | null
          output_width: number | null
          project_id: string
          render_error: string | null
          render_status: string
          score: number | null
          score_breakdown: Json
          seq: number
          source_video_id: string | null
          start_seconds: number
          thumbnail_path: string | null
          title: string | null
          transcript_text: string | null
          updated_at: string
          user_id: string
          validated: boolean
        }
        Insert: {
          candidate_id?: string | null
          caption_settings?: Json
          captions_enabled?: boolean
          category?: string | null
          created_at?: string
          crop_settings?: Json
          description?: string | null
          duration_seconds?: number | null
          end_seconds: number
          explanation?: string | null
          file_size_bytes?: number | null
          hashtags?: string[] | null
          hook?: string | null
          id?: string
          language?: string | null
          output_height?: number | null
          output_path?: string | null
          output_width?: number | null
          project_id: string
          render_error?: string | null
          render_status?: string
          score?: number | null
          score_breakdown?: Json
          seq?: number
          source_video_id?: string | null
          start_seconds: number
          thumbnail_path?: string | null
          title?: string | null
          transcript_text?: string | null
          updated_at?: string
          user_id: string
          validated?: boolean
        }
        Update: {
          candidate_id?: string | null
          caption_settings?: Json
          captions_enabled?: boolean
          category?: string | null
          created_at?: string
          crop_settings?: Json
          description?: string | null
          duration_seconds?: number | null
          end_seconds?: number
          explanation?: string | null
          file_size_bytes?: number | null
          hashtags?: string[] | null
          hook?: string | null
          id?: string
          language?: string | null
          output_height?: number | null
          output_path?: string | null
          output_width?: number | null
          project_id?: string
          render_error?: string | null
          render_status?: string
          score?: number | null
          score_breakdown?: Json
          seq?: number
          source_video_id?: string | null
          start_seconds?: number
          thumbnail_path?: string | null
          title?: string | null
          transcript_text?: string | null
          updated_at?: string
          user_id?: string
          validated?: boolean
        }
        Relationships: [
          {
            foreignKeyName: "shorts_candidate_id_fkey"
            columns: ["candidate_id"]
            isOneToOne: false
            referencedRelation: "clip_candidates"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "shorts_project_id_fkey"
            columns: ["project_id"]
            isOneToOne: false
            referencedRelation: "projects"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "shorts_source_video_id_fkey"
            columns: ["source_video_id"]
            isOneToOne: false
            referencedRelation: "source_videos"
            referencedColumns: ["id"]
          },
        ]
      }
      source_videos: {
        Row: {
          audio_codec: string | null
          checksum: string | null
          created_at: string
          duration_seconds: number | null
          fps: number | null
          has_audio: boolean | null
          height: number | null
          id: string
          original_filename: string | null
          project_id: string
          rotation: number | null
          size_bytes: number | null
          storage_path: string | null
          user_id: string
          video_codec: string | null
          width: number | null
        }
        Insert: {
          audio_codec?: string | null
          checksum?: string | null
          created_at?: string
          duration_seconds?: number | null
          fps?: number | null
          has_audio?: boolean | null
          height?: number | null
          id?: string
          original_filename?: string | null
          project_id: string
          rotation?: number | null
          size_bytes?: number | null
          storage_path?: string | null
          user_id: string
          video_codec?: string | null
          width?: number | null
        }
        Update: {
          audio_codec?: string | null
          checksum?: string | null
          created_at?: string
          duration_seconds?: number | null
          fps?: number | null
          has_audio?: boolean | null
          height?: number | null
          id?: string
          original_filename?: string | null
          project_id?: string
          rotation?: number | null
          size_bytes?: number | null
          storage_path?: string | null
          user_id?: string
          video_codec?: string | null
          width?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "source_videos_project_id_fkey"
            columns: ["project_id"]
            isOneToOne: false
            referencedRelation: "projects"
            referencedColumns: ["id"]
          },
        ]
      }
      transcript_segments: {
        Row: {
          confidence: number | null
          created_at: string
          end_seconds: number
          id: string
          idx: number
          kind: string
          start_seconds: number
          text: string
          transcript_id: string
          user_id: string
          words: Json | null
        }
        Insert: {
          confidence?: number | null
          created_at?: string
          end_seconds: number
          id?: string
          idx: number
          kind?: string
          start_seconds: number
          text: string
          transcript_id: string
          user_id: string
          words?: Json | null
        }
        Update: {
          confidence?: number | null
          created_at?: string
          end_seconds?: number
          id?: string
          idx?: number
          kind?: string
          start_seconds?: number
          text?: string
          transcript_id?: string
          user_id?: string
          words?: Json | null
        }
        Relationships: [
          {
            foreignKeyName: "transcript_segments_transcript_id_fkey"
            columns: ["transcript_id"]
            isOneToOne: false
            referencedRelation: "transcripts"
            referencedColumns: ["id"]
          },
        ]
      }
      transcripts: {
        Row: {
          created_at: string
          full_text: string | null
          has_speech: boolean
          id: string
          language: string | null
          language_confidence: number | null
          model: string | null
          project_id: string
          source_video_id: string | null
          user_id: string
          word_count: number | null
        }
        Insert: {
          created_at?: string
          full_text?: string | null
          has_speech?: boolean
          id?: string
          language?: string | null
          language_confidence?: number | null
          model?: string | null
          project_id: string
          source_video_id?: string | null
          user_id: string
          word_count?: number | null
        }
        Update: {
          created_at?: string
          full_text?: string | null
          has_speech?: boolean
          id?: string
          language?: string | null
          language_confidence?: number | null
          model?: string | null
          project_id?: string
          source_video_id?: string | null
          user_id?: string
          word_count?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "transcripts_project_id_fkey"
            columns: ["project_id"]
            isOneToOne: false
            referencedRelation: "projects"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "transcripts_source_video_id_fkey"
            columns: ["source_video_id"]
            isOneToOne: false
            referencedRelation: "source_videos"
            referencedColumns: ["id"]
          },
        ]
      }
      user_settings: {
        Row: {
          ai_model: string | null
          ai_provider: string
          compute_preference: string
          created_at: string
          default_caption_style: string
          default_clip_length: string
          default_quality_mode: string
          language: string
          max_concurrent_renders: number
          output_resolution: string
          temp_retention_hours: number
          theme: string
          updated_at: string
          user_id: string
          whisper_model: string
        }
        Insert: {
          ai_model?: string | null
          ai_provider?: string
          compute_preference?: string
          created_at?: string
          default_caption_style?: string
          default_clip_length?: string
          default_quality_mode?: string
          language?: string
          max_concurrent_renders?: number
          output_resolution?: string
          temp_retention_hours?: number
          theme?: string
          updated_at?: string
          user_id: string
          whisper_model?: string
        }
        Update: {
          ai_model?: string | null
          ai_provider?: string
          compute_preference?: string
          created_at?: string
          default_caption_style?: string
          default_clip_length?: string
          default_quality_mode?: string
          language?: string
          max_concurrent_renders?: number
          output_resolution?: string
          temp_retention_hours?: number
          theme?: string
          updated_at?: string
          user_id?: string
          whisper_model?: string
        }
        Relationships: []
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends (DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never) = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends (PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never) = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {},
  },
} as const
