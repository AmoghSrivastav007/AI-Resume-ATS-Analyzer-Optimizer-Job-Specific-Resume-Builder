-- Step 4: Add score_breakdown column for explainability tree

ALTER TABLE public.resume_analyses
  ADD COLUMN IF NOT EXISTS score_breakdown JSONB NOT NULL DEFAULT '{}'::jsonb;

COMMENT ON COLUMN public.resume_analyses.score_breakdown IS 'Explainability tree showing category scores and deductions';
