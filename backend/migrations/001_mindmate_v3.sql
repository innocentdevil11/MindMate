-- =============================================================
-- MindMate v3 — Database Migration
-- Run this in Supabase SQL Editor (Dashboard → SQL Editor → New query)
-- =============================================================

-- 1. Enable pgvector extension (required for episodic memory embeddings)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Messages table (short-term memory — last N messages per conversation)
CREATE TABLE IF NOT EXISTS messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    conversation_id UUID NOT NULL,
    user_id UUID NOT NULL REFERENCES auth.users(id),
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at DESC);
CREATE INDEX idx_messages_user ON messages(user_id);

-- 3. Episodic memory (vector-based long-term memory)
CREATE TABLE IF NOT EXISTS episodic_memory (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id),
    content TEXT NOT NULL,
    embedding vector(384),  -- all-MiniLM-L6-v2 produces 384-dim embeddings
    importance_score FLOAT DEFAULT 0.5 CHECK (importance_score >= 0 AND importance_score <= 1),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_episodic_user ON episodic_memory(user_id);
-- Cosine similarity index for fast vector search
CREATE INDEX idx_episodic_embedding ON episodic_memory
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- 4. User profile (semantic long-term user model)
CREATE TABLE IF NOT EXISTS user_profile (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id),
    important_people JSONB DEFAULT '[]'::jsonb,
    goals JSONB DEFAULT '[]'::jsonb,
    preferences JSONB DEFAULT '{}'::jsonb,
    recurring_issues JSONB DEFAULT '[]'::jsonb,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 5. Brain config (per-conversation brain weights)
CREATE TABLE IF NOT EXISTS brain_config (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    conversation_id UUID NOT NULL,
    user_id UUID NOT NULL REFERENCES auth.users(id),
    weights JSONB NOT NULL DEFAULT '{
        "analytical": 0.2,
        "emotional": 0.2,
        "ethical": 0.2,
        "values": 0.2,
        "red_team": 0.0
    }'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE UNIQUE INDEX idx_brain_config_conversation ON brain_config(conversation_id);
CREATE INDEX idx_brain_config_user ON brain_config(user_id);

-- 6. Thinking trace (internal reasoning visualization)
CREATE TABLE IF NOT EXISTS thinking_trace (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    conversation_id UUID NOT NULL,
    message_id UUID NOT NULL,
    step_type TEXT NOT NULL,
    agent TEXT,  -- NULL for non-agent steps (intent, complexity, etc.)
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_trace_conversation ON thinking_trace(conversation_id, created_at);
CREATE INDEX idx_trace_message ON thinking_trace(message_id);

-- 7. Feedback v2 (structured feedback with brain config snapshot)
CREATE TABLE IF NOT EXISTS feedback_v2 (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id),
    conversation_id UUID NOT NULL,
    message_id UUID NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    feedback_type TEXT NOT NULL,
    text_feedback TEXT,
    brain_config JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_feedback_v2_user ON feedback_v2(user_id, created_at DESC);
CREATE INDEX idx_feedback_v2_conversation ON feedback_v2(conversation_id);

-- 8. Evolved brain defaults (adaptive brain evolution results)
CREATE TABLE IF NOT EXISTS evolved_brain_defaults (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id),
    preferred_weights JSONB NOT NULL DEFAULT '{
        "analytical": 0.2,
        "emotional": 0.2,
        "ethical": 0.2,
        "values": 0.2,
        "red_team": 0.0
    }'::jsonb,
    sample_count INT DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 9. Helper function: cosine similarity search for episodic memory
CREATE OR REPLACE FUNCTION match_episodic_memories(
    query_embedding vector(384),
    match_user_id UUID,
    match_count INT DEFAULT 5,
    match_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    importance_score FLOAT,
    similarity FLOAT
)
LANGUAGE sql STABLE
AS $$
    SELECT
        em.id,
        em.content,
        em.importance_score,
        1 - (em.embedding <=> query_embedding) AS similarity
    FROM episodic_memory em
    WHERE em.user_id = match_user_id
        AND 1 - (em.embedding <=> query_embedding) > match_threshold
    ORDER BY em.embedding <=> query_embedding
    LIMIT match_count;
$$;
