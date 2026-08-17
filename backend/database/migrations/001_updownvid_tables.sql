-- UpDownVid Supabase Schema
-- Run this after MCP is reconnected to the Nothing project

-- 1. youtube_connections: Stores Google OAuth tokens per user
CREATE TABLE IF NOT EXISTS public.youtube_connections (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    google_user_id TEXT,
    google_email TEXT,
    google_name TEXT,
    google_avatar_url TEXT,
    youtube_channel_id TEXT,
    youtube_channel_name TEXT,
    youtube_channel_thumbnail TEXT,
    youtube_subscriber_count BIGINT DEFAULT 0,
    youtube_video_count BIGINT DEFAULT 0,
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMPTZ,
    token_scope TEXT,
    connected_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id)
);

-- 2. user_settings: User preferences
CREATE TABLE IF NOT EXISTS public.user_settings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    monitor_interval INTEGER DEFAULT 300,
    quality TEXT DEFAULT '1080p',
    metadata_mode TEXT DEFAULT 'original',
    custom_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id)
);

-- 3. monitored_channels: YouTube channels being monitored
CREATE TABLE IF NOT EXISTS public.monitored_channels (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    channel_url TEXT NOT NULL,
    channel_id TEXT,
    channel_name TEXT,
    channel_thumbnail TEXT,
    channel_description TEXT,
    subscriber_count BIGINT DEFAULT 0,
    video_count BIGINT DEFAULT 0,
    last_checked_at TIMESTAMPTZ,
    last_video_id TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 4. upload_history: Record of YouTube uploads
CREATE TABLE IF NOT EXISTS public.upload_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    youtube_video_id TEXT,
    youtube_video_url TEXT,
    original_url TEXT,
    title TEXT,
    description TEXT,
    thumbnail TEXT,
    duration TEXT,
    platform TEXT,
    status TEXT DEFAULT 'completed',
    uploaded_at TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 5. download_jobs: Track download activity
CREATE TABLE IF NOT EXISTS public.download_jobs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    url TEXT NOT NULL,
    platform TEXT,
    quality TEXT,
    title TEXT,
    file_path TEXT,
    file_size BIGINT,
    status TEXT DEFAULT 'pending',
    error_message TEXT,
    started_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 6. automation_logs: Scan pipeline logs
CREATE TABLE IF NOT EXISTS public.automation_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    channel_id UUID REFERENCES public.monitored_channels(id) ON DELETE CASCADE,
    level TEXT DEFAULT 'info',
    message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 7. channel_analytics_cache: Cached YouTube Analytics data
CREATE TABLE IF NOT EXISTS public.channel_analytics_cache (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    channel_id TEXT NOT NULL,
    period TEXT NOT NULL,
    date_range_start DATE,
    date_range_end DATE,
    metrics JSONB DEFAULT '{}'::jsonb,
    top_videos JSONB DEFAULT '[]'::jsonb,
    traffic_sources JSONB DEFAULT '[]'::jsonb,
    audience_data JSONB DEFAULT '{}'::jsonb,
    cached_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ,
    UNIQUE(user_id, channel_id, period, date_range_start, date_range_end)
);

-- 8. automation_status: Service status per user
CREATE TABLE IF NOT EXISTS public.automation_status (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT false,
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_youtube_connections_user ON public.youtube_connections(user_id);
CREATE INDEX IF NOT EXISTS idx_user_settings_user ON public.user_settings(user_id);
CREATE INDEX IF NOT EXISTS idx_monitored_channels_user ON public.monitored_channels(user_id);
CREATE INDEX IF NOT EXISTS idx_monitored_channels_active ON public.monitored_channels(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_upload_history_user ON public.upload_history(user_id);
CREATE INDEX IF NOT EXISTS idx_download_jobs_user ON public.download_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_automation_logs_user ON public.automation_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_automation_logs_channel ON public.automation_logs(channel_id);
CREATE INDEX IF NOT EXISTS idx_analytics_cache_user_channel ON public.channel_analytics_cache(user_id, channel_id);
CREATE INDEX IF NOT EXISTS idx_automation_status_user ON public.automation_status(user_id);

-- RLS Policies
ALTER TABLE public.youtube_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.monitored_channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.upload_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.download_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.automation_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.channel_analytics_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.automation_status ENABLE ROW LEVEL SECURITY;

-- youtube_connections: users can only access their own
CREATE POLICY "Users can view own youtube connection" ON public.youtube_connections
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own youtube connection" ON public.youtube_connections
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own youtube connection" ON public.youtube_connections
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own youtube connection" ON public.youtube_connections
    FOR DELETE USING (auth.uid() = user_id);

-- user_settings: users can only access their own
CREATE POLICY "Users can view own settings" ON public.user_settings
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own settings" ON public.user_settings
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own settings" ON public.user_settings
    FOR UPDATE USING (auth.uid() = user_id);

-- monitored_channels: users can only access their own
CREATE POLICY "Users can view own channels" ON public.monitored_channels
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own channels" ON public.monitored_channels
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own channels" ON public.monitored_channels
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own channels" ON public.monitored_channels
    FOR DELETE USING (auth.uid() = user_id);

-- upload_history: users can only access their own
CREATE POLICY "Users can view own history" ON public.upload_history
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own history" ON public.upload_history
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- download_jobs: users can only access their own
CREATE POLICY "Users can view own downloads" ON public.download_jobs
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own downloads" ON public.download_jobs
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own downloads" ON public.download_jobs
    FOR UPDATE USING (auth.uid() = user_id);

-- automation_logs: users can only access their own
CREATE POLICY "Users can view own automation logs" ON public.automation_logs
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own automation logs" ON public.automation_logs
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can delete own automation logs" ON public.automation_logs
    FOR DELETE USING (auth.uid() = user_id);

-- channel_analytics_cache: users can only access their own
CREATE POLICY "Users can view own analytics" ON public.channel_analytics_cache
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can upsert own analytics" ON public.channel_analytics_cache
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own analytics" ON public.channel_analytics_cache
    FOR UPDATE USING (auth.uid() = user_id);

-- automation_status: users can only access their own
CREATE POLICY "Users can view own automation status" ON public.automation_status
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own automation status" ON public.automation_status
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own automation status" ON public.automation_status
    FOR UPDATE USING (auth.uid() = user_id);

-- Service role bypass (for backend operations)
CREATE POLICY "Service role full access youtube_connections" ON public.youtube_connections
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access user_settings" ON public.user_settings
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access monitored_channels" ON public.monitored_channels
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access upload_history" ON public.upload_history
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access download_jobs" ON public.download_jobs
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access automation_logs" ON public.automation_logs
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access channel_analytics_cache" ON public.channel_analytics_cache
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access automation_status" ON public.automation_status
    FOR ALL USING (auth.role() = 'service_role');
