-- 002_chat_persistence.sql
-- MindMate V3 Chat Persistence Migration

CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id),
    title TEXT,
    brain_config JSONB DEFAULT '{}'::jsonb,
    tone_config TEXT DEFAULT 'clean',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id, updated_at DESC);
