-- Step 2: OCR flag, parse error, languages section type

ALTER TABLE public.resume_versions
  ADD COLUMN IF NOT EXISTS needs_ocr BOOLEAN NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS parse_error TEXT;

ALTER TABLE public.resume_sections
  DROP CONSTRAINT IF EXISTS resume_sections_section_type_check;

ALTER TABLE public.resume_sections
  ADD CONSTRAINT resume_sections_section_type_check
  CHECK (
    section_type IN (
      'contact', 'summary', 'experience', 'education',
      'skills', 'projects', 'certifications', 'languages', 'other'
    )
  );
