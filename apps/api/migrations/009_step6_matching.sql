-- Step 6: Matching Engine + JD Match Score

-- Skill aliases table for Layer 2 matching
CREATE TABLE IF NOT EXISTS public.skill_aliases (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  canonical_term TEXT NOT NULL,
  alias_term TEXT NOT NULL,
  source TEXT DEFAULT 'ESCO',  -- ESCO, O*NET, manual
  confidence NUMERIC(3,2) DEFAULT 1.0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(canonical_term, alias_term)
);

-- Indexes for fast lookup
CREATE INDEX idx_skill_aliases_canonical ON public.skill_aliases(LOWER(canonical_term));
CREATE INDEX idx_skill_aliases_alias ON public.skill_aliases(LOWER(alias_term));

-- Update match_results to support 5 match categories and evidence
ALTER TABLE public.match_results 
  DROP CONSTRAINT IF EXISTS match_results_match_status_check;

ALTER TABLE public.match_results
  ADD CONSTRAINT match_results_match_status_check CHECK (
    match_status IN ('matched', 'partially_matched', 'missing', 'weak_evidence', 'not_relevant')
  );

-- Add evidence_block_id and recommendation fields
ALTER TABLE public.match_results
  ADD COLUMN IF NOT EXISTS evidence_block_id UUID REFERENCES public.resume_blocks(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS recommendation TEXT,
  ADD COLUMN IF NOT EXISTS match_layer INT CHECK (match_layer BETWEEN 1 AND 4),  -- Which layer matched
  ADD COLUMN IF NOT EXISTS similarity_score NUMERIC(5,4);  -- For Layer 3 semantic matching

-- Add embedding column to job_requirements if not exists (for Step 5 table)
ALTER TABLE public.job_requirements
  ADD COLUMN IF NOT EXISTS embedding vector(1536);

-- Create HNSW index for job_requirements embeddings
CREATE INDEX IF NOT EXISTS idx_job_requirements_embedding_hnsw
  ON public.job_requirements USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64)
  WHERE embedding IS NOT NULL;

-- Add jd_match_score and match_breakdown to resume_analyses
ALTER TABLE public.resume_analyses
  ADD COLUMN IF NOT EXISTS jd_match_score NUMERIC(5,2),
  ADD COLUMN IF NOT EXISTS match_breakdown JSONB NOT NULL DEFAULT '{}'::jsonb;

-- Indexes for match queries
CREATE INDEX IF NOT EXISTS idx_match_results_analysis_id ON public.match_results(resume_analysis_id);
CREATE INDEX IF NOT EXISTS idx_match_results_match_status ON public.match_results(match_status);
CREATE INDEX IF NOT EXISTS idx_match_results_evidence_block ON public.match_results(evidence_block_id) WHERE evidence_block_id IS NOT NULL;

-- RLS for skill_aliases (read-only for all authenticated users)
ALTER TABLE public.skill_aliases ENABLE ROW LEVEL SECURITY;

CREATE POLICY skill_aliases_read_all ON public.skill_aliases
  FOR SELECT USING (auth.uid() IS NOT NULL);

-- Updated_at trigger for skill_aliases
CREATE TRIGGER set_skill_aliases_updated_at BEFORE UPDATE ON public.skill_aliases
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Seed common tech/business skill aliases from ESCO/O*NET taxonomy
-- This is a starter set - can be expanded later
INSERT INTO public.skill_aliases (canonical_term, alias_term, source, confidence) VALUES
  -- Programming Languages
  ('JavaScript', 'JS', 'ESCO', 1.0),
  ('JavaScript', 'ECMAScript', 'ESCO', 0.95),
  ('TypeScript', 'TS', 'ESCO', 1.0),
  ('Python', 'Python3', 'ESCO', 0.95),
  ('C#', 'CSharp', 'ESCO', 1.0),
  ('C#', 'C Sharp', 'ESCO', 1.0),
  ('C++', 'CPlusPlus', 'ESCO', 1.0),
  ('Objective-C', 'Objective C', 'ESCO', 1.0),
  
  -- Frameworks & Libraries
  ('React', 'ReactJS', 'ESCO', 1.0),
  ('React', 'React.js', 'ESCO', 1.0),
  ('Angular', 'AngularJS', 'ESCO', 0.90),
  ('Vue', 'VueJS', 'ESCO', 1.0),
  ('Vue', 'Vue.js', 'ESCO', 1.0),
  ('Node.js', 'NodeJS', 'ESCO', 1.0),
  ('Node.js', 'Node', 'ESCO', 0.95),
  ('Express', 'ExpressJS', 'ESCO', 1.0),
  ('Express', 'Express.js', 'ESCO', 1.0),
  ('Django', 'Django Framework', 'ESCO', 0.95),
  ('Flask', 'Flask Framework', 'ESCO', 0.95),
  ('Spring', 'Spring Framework', 'ESCO', 0.95),
  ('Spring Boot', 'SpringBoot', 'ESCO', 1.0),
  ('.NET', 'DotNet', 'ESCO', 1.0),
  ('.NET', 'Dot Net', 'ESCO', 1.0),
  ('ASP.NET', 'ASP Dot Net', 'ESCO', 1.0),
  
  -- Databases
  ('PostgreSQL', 'Postgres', 'ESCO', 1.0),
  ('PostgreSQL', 'PGSQL', 'ESCO', 0.95),
  ('MySQL', 'My SQL', 'ESCO', 1.0),
  ('MongoDB', 'Mongo', 'ESCO', 0.95),
  ('Microsoft SQL Server', 'SQL Server', 'ESCO', 1.0),
  ('Microsoft SQL Server', 'MSSQL', 'ESCO', 1.0),
  ('Oracle Database', 'Oracle DB', 'ESCO', 0.95),
  ('Redis', 'Redis Cache', 'ESCO', 0.90),
  
  -- Cloud Platforms
  ('Amazon Web Services', 'AWS', 'ESCO', 1.0),
  ('Google Cloud Platform', 'GCP', 'ESCO', 1.0),
  ('Microsoft Azure', 'Azure', 'ESCO', 1.0),
  ('Amazon EC2', 'EC2', 'ESCO', 1.0),
  ('Amazon S3', 'S3', 'ESCO', 1.0),
  ('Amazon RDS', 'RDS', 'ESCO', 1.0),
  ('AWS Lambda', 'Lambda', 'ESCO', 0.85),
  
  -- DevOps & Tools
  ('Continuous Integration', 'CI', 'O*NET', 1.0),
  ('Continuous Deployment', 'CD', 'O*NET', 1.0),
  ('CI/CD', 'Continuous Integration/Continuous Deployment', 'O*NET', 1.0),
  ('Docker', 'Docker Container', 'ESCO', 0.95),
  ('Kubernetes', 'K8s', 'ESCO', 1.0),
  ('Jenkins', 'Jenkins CI', 'ESCO', 0.95),
  ('Git', 'Git Version Control', 'ESCO', 0.95),
  ('GitHub', 'Git Hub', 'ESCO', 1.0),
  ('GitLab', 'Git Lab', 'ESCO', 1.0),
  
  -- Methodologies
  ('Agile', 'Agile Methodology', 'O*NET', 0.95),
  ('Scrum', 'Scrum Framework', 'O*NET', 0.95),
  ('Kanban', 'Kanban Method', 'O*NET', 0.95),
  ('Test Driven Development', 'TDD', 'O*NET', 1.0),
  ('Behavior Driven Development', 'BDD', 'O*NET', 1.0),
  
  -- Testing
  ('Jest', 'Jest Testing', 'ESCO', 0.95),
  ('Mocha', 'Mocha Testing', 'ESCO', 0.95),
  ('PyTest', 'Pytest', 'ESCO', 1.0),
  ('JUnit', 'JUnit Testing', 'ESCO', 0.95),
  ('Selenium', 'Selenium WebDriver', 'ESCO', 0.95),
  
  -- Data & Analytics
  ('Machine Learning', 'ML', 'O*NET', 1.0),
  ('Artificial Intelligence', 'AI', 'O*NET', 1.0),
  ('Natural Language Processing', 'NLP', 'O*NET', 1.0),
  ('Data Science', 'Data Analytics', 'O*NET', 0.85),
  ('Business Intelligence', 'BI', 'O*NET', 1.0),
  ('Extract Transform Load', 'ETL', 'O*NET', 1.0),
  
  -- Frontend Technologies
  ('HTML', 'HTML5', 'ESCO', 0.95),
  ('CSS', 'CSS3', 'ESCO', 0.95),
  ('Cascading Style Sheets', 'CSS', 'ESCO', 1.0),
  ('Sass', 'SCSS', 'ESCO', 0.95),
  ('Webpack', 'Webpack Bundler', 'ESCO', 0.95),
  
  -- Backend & APIs
  ('RESTful API', 'REST API', 'ESCO', 1.0),
  ('RESTful API', 'RESTful', 'ESCO', 0.95),
  ('GraphQL', 'Graph QL', 'ESCO', 1.0),
  ('gRPC', 'Google RPC', 'ESCO', 0.90),
  ('Microservices', 'Micro Services', 'O*NET', 1.0),
  
  -- Mobile Development
  ('iOS Development', 'iOS Dev', 'O*NET', 0.95),
  ('Android Development', 'Android Dev', 'O*NET', 0.95),
  ('React Native', 'ReactNative', 'ESCO', 1.0),
  ('Swift', 'Swift Programming', 'ESCO', 0.90),
  ('Kotlin', 'Kotlin Programming', 'ESCO', 0.90),
  
  -- Business Skills
  ('Project Management', 'PM', 'O*NET', 0.90),
  ('Stakeholder Management', 'Stakeholder Engagement', 'O*NET', 0.95),
  ('Cross-functional Collaboration', 'Cross-functional Teams', 'O*NET', 0.95),
  ('Problem Solving', 'Analytical Thinking', 'O*NET', 0.85),
  ('Communication Skills', 'Effective Communication', 'O*NET', 0.90),
  ('Leadership', 'Team Leadership', 'O*NET', 0.90),
  ('Time Management', 'Prioritization', 'O*NET', 0.85),
  
  -- Certifications (common abbreviations)
  ('AWS Certified Solutions Architect', 'AWS CSA', 'O*NET', 1.0),
  ('Project Management Professional', 'PMP', 'O*NET', 1.0),
  ('Certified Kubernetes Administrator', 'CKA', 'O*NET', 1.0),
  ('Certified ScrumMaster', 'CSM', 'O*NET', 1.0),
  ('Google Cloud Professional', 'GCP Professional', 'O*NET', 0.95)
ON CONFLICT (canonical_term, alias_term) DO NOTHING;

COMMENT ON TABLE public.skill_aliases IS 'Skill taxonomy aliases for Layer 2 matching (ESCO/O*NET based)';
COMMENT ON COLUMN public.skill_aliases.canonical_term IS 'Normalized canonical skill name';
COMMENT ON COLUMN public.skill_aliases.alias_term IS 'Alternative name or abbreviation';
COMMENT ON COLUMN public.skill_aliases.confidence IS 'Confidence score for alias mapping (0.0-1.0)';

