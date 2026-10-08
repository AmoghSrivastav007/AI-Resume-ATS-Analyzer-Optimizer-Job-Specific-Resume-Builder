-- Migration 010: Export Jobs Table
-- Tracks resume export generation status and results

CREATE TABLE IF NOT EXISTS export_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    resume_version_id UUID NOT NULL REFERENCES resume_versions(id) ON DELETE CASCADE,
    format TEXT NOT NULL CHECK (format IN ('pdf', 'docx')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'generating', 'validating', 'completed', 'failed')),
    storage_path TEXT,
    error_message TEXT,
    
    -- Self-check validation results
    validation_passed BOOLEAN,
    validation_details JSONB DEFAULT '{}',
    
    -- Metadata
    file_size_bytes INTEGER,
    generated_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_export_jobs_user_id ON export_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_export_jobs_resume_version_id ON export_jobs(resume_version_id);
CREATE INDEX IF NOT EXISTS idx_export_jobs_status ON export_jobs(status);

-- RLS Policies
ALTER TABLE export_jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own export jobs"
    ON export_jobs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create export jobs for their resumes"
    ON export_jobs FOR INSERT
    WITH CHECK (
        auth.uid() = user_id
        AND EXISTS (
            SELECT 1 FROM resume_versions
            WHERE id = resume_version_id
            AND user_id = auth.uid()
        )
    );

-- Updated trigger
CREATE TRIGGER update_export_jobs_updated_at
    BEFORE UPDATE ON export_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
