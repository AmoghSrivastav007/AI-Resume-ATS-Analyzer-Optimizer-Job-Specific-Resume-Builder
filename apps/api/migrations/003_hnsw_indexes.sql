-- HNSW indexes for pgvector embedding columns (§9)

CREATE INDEX idx_resume_blocks_embedding_hnsw
  ON public.resume_blocks USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64)
  WHERE embedding IS NOT NULL;

CREATE INDEX idx_fact_ledger_entries_embedding_hnsw
  ON public.fact_ledger_entries USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64)
  WHERE embedding IS NOT NULL;

CREATE INDEX idx_experiences_embedding_hnsw
  ON public.experiences USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64)
  WHERE embedding IS NOT NULL;

CREATE INDEX idx_educations_embedding_hnsw
  ON public.educations USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64)
  WHERE embedding IS NOT NULL;

CREATE INDEX idx_certifications_embedding_hnsw
  ON public.certifications USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64)
  WHERE embedding IS NOT NULL;

CREATE INDEX idx_projects_embedding_hnsw
  ON public.projects USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64)
  WHERE embedding IS NOT NULL;

CREATE INDEX idx_skills_embedding_hnsw
  ON public.skills USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64)
  WHERE embedding IS NOT NULL;

CREATE INDEX idx_job_descriptions_embedding_hnsw
  ON public.job_descriptions USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64)
  WHERE embedding IS NOT NULL;

CREATE INDEX idx_job_requirements_embedding_hnsw
  ON public.job_requirements USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64)
  WHERE embedding IS NOT NULL;
