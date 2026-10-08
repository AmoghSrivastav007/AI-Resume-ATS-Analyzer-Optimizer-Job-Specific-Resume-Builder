-- Step 5: Job postings and requirements tables

-- Job postings table (replaces/extends job_descriptions)
CREATE TABLE IF NOT EXISTS public.job_postings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  company TEXT,
  source_url TEXT,
  raw_text TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Job requirements table (categorized extraction)
CREATE TABLE IF NOT EXISTS public.job_requirements (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  job_posting_id UUID NOT NULL REFERENCES public.job_postings(id) ON DELETE CASCADE,
  requirement_type TEXT NOT NULL CHECK (
    requirement_type IN (
      'required_skill',
      'preferred_skill',
      'responsibility',
      'education',
      'experience_years',
      'certification',
      'domain_knowledge',
      'competency_signal'
    )
  ),
  requirement_text TEXT NOT NULL,
  category TEXT,  -- Optional grouping
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.job_postings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.job_requirements ENABLE ROW LEVEL SECURITY;

-- RLS policies
CREATE POLICY job_postings_all_own ON public.job_postings
  FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE POLICY job_requirements_all_own ON public.job_requirements
  FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Indexes
CREATE INDEX idx_job_postings_user_id ON public.job_postings(user_id);
CREATE INDEX idx_job_requirements_posting_id ON public.job_requirements(job_posting_id);
CREATE INDEX idx_job_requirements_type ON public.job_requirements(requirement_type);

-- Updated_at triggers
CREATE TRIGGER set_job_postings_updated_at BEFORE UPDATE ON public.job_postings
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER set_job_requirements_updated_at BEFORE UPDATE ON public.job_requirements
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

COMMENT ON TABLE public.job_postings IS 'User-created job postings from pasted text or uploaded files';
COMMENT ON TABLE public.job_requirements IS 'Structured requirements extracted from job postings by LLM';
COMMENT ON COLUMN public.job_requirements.requirement_type IS 'Type of requirement: required_skill, preferred_skill, responsibility, education, experience_years, certification, domain_knowledge, competency_signal';
