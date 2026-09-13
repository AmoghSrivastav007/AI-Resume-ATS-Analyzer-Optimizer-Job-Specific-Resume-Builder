# Resume ATS Analyzer & Optimizer — Technical Blueprint

## §4 Product Architecture

Monorepo with two deployable apps:

- **apps/web** — Next.js (App Router) frontend. Handles auth UI, resume upload, and (later) editor/analysis views. Talks to Supabase Auth directly and to the FastAPI backend for business logic.
- **apps/api** — FastAPI backend. Validates Supabase JWTs, enforces business rules, writes to Postgres via Supabase service role or authenticated client, stores files in Supabase Storage, and (later) enqueues RQ jobs.

Data flow for Step 1 (upload):

```
Browser → Supabase Auth (signup/login)
Browser → POST /api/resumes (JWT + file) → FastAPI
FastAPI → content-sniff validate → Supabase Storage → Postgres (resumes + resume_versions)
```

External services: Supabase (Auth, Postgres, Storage, RLS), Redis (queue, Step 2+), Anthropic API (Step 2+).

---

## §5 Resume Parsing Strategy

Six-step pipeline in `apps/api/services/parser/`. Runs asynchronously via Redis + RQ after upload.

### Step 1 — File intake & sanitization

- **Virus scan hook**: `VirusScanner` protocol; `NoOpVirusScanner` when `VIRUS_SCAN_URL` is unset (logs TODO). Swap to HTTP/ClamAV implementation via env — one-line factory change.
- **Magic-byte validation**: Re-validate PDF (`%PDF`) / DOCX (ZIP + `word/document.xml`) — never trust extension.
- **DOCX macro stripping**: Remove `word/vbaProject.bin`, `word/vbaData.xml`, and `ActiveX/` entries from the ZIP before parsing.

### Step 2 — Text-layer check (PDF only)

- PyMuPDF extracts per-page character counts.
- If `total_chars / page_count < 50` (and `page_count >= 1`), set `resume_versions.needs_ocr = true`, `status = error`, store user message, **stop** — no OCR in MVP (§16).

User-facing error: *"This looks like a scanned resume. OCR support is coming soon — please upload a text-based PDF or DOCX."*

### Step 3 — Deterministic structural extraction

- **PDF**: PyMuPDF text blocks with bbox, page, font name, font size.
- **DOCX**: `python-docx` paragraph/run structure + `mammoth` plain-text fallback.

Output: `StructuralDocument` (plain text + typed blocks with layout metadata for later formatting checks).

### Step 4 — LLM structured extraction

- Single Anthropic call using **Haiku-class model** (`ANTHROPIC_HAIKU_MODEL` env var).
- Tool-use / structured output with strict Pydantic schema — **never** free-text parse.
- Fields: `contact`, `summary`, `skills`, `work_experience`, `education`, `certifications`, `projects`, `languages`.

### Step 5 — Cross-validation

- Regex extracts emails, phones, dates from plain text.
- Reconcile against LLM fields; on disagreement mark field `confidence: "low"` and store both values in metadata — do not silently pick one.

### Step 6 — Persist

Populate in section order:

1. contact → 2. summary → 3. experience → 4. education → 5. skills → 6. projects → 7. certifications → 8. languages

Tables: `resume_sections`, `resume_blocks`, `fact_ledger_entries` (dates, titles, skills, metrics, certifications).

On success: `resume_versions.status = parsed`. Job result available via `GET /api/jobs/{id}`; full structure via `GET /api/resumes/{id}`.

---

## §9 Database Schema

All tables live in `public`. Every table has `created_at TIMESTAMPTZ NOT NULL DEFAULT now()` and `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()` with a trigger to auto-update `updated_at`.

Embedding dimension: **1536** (Anthropic / OpenAI-compatible). HNSW indexes use `vector_cosine_ops`.

### Extensions

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
```

### users

Profile row synced from Supabase Auth.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | FK → auth.users(id) ON DELETE CASCADE |
| email | TEXT NOT NULL | |
| full_name | TEXT | nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### resumes

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | default uuid_generate_v4() |
| user_id | UUID NOT NULL | FK → users(id) |
| title | TEXT NOT NULL | defaults to uploaded filename |
| current_version_id | UUID | FK → resume_versions(id), nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### resume_versions

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| resume_id | UUID NOT NULL | FK → resumes(id) ON DELETE CASCADE |
| user_id | UUID NOT NULL | FK → users(id) |
| version_number | INT NOT NULL | starts at 1 |
| status | TEXT NOT NULL | draft \| parsing \| parsed \| error |
| storage_path | TEXT NOT NULL | Supabase Storage object path |
| original_filename | TEXT NOT NULL | |
| mime_type | TEXT NOT NULL | application/pdf or docx mime |
| file_size_bytes | INT NOT NULL | |
| needs_ocr | BOOLEAN NOT NULL DEFAULT false | true when scanned/image PDF detected |
| parse_error | TEXT | user-facing or internal parse failure message |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

Unique: `(resume_id, version_number)`.

### resume_sections

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| resume_version_id | UUID NOT NULL | FK → resume_versions(id) ON DELETE CASCADE |
| user_id | UUID NOT NULL | FK → users(id) |
| section_type | TEXT NOT NULL | contact \| summary \| experience \| education \| skills \| projects \| certifications \| languages \| other |
| title | TEXT | nullable |
| sort_order | INT NOT NULL DEFAULT 0 | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### resume_blocks

Atomic content blocks within a section (used by editor + Truth Guard).

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| resume_version_id | UUID NOT NULL | FK → resume_versions(id) ON DELETE CASCADE |
| section_id | UUID NOT NULL | FK → resume_sections(id) ON DELETE CASCADE |
| user_id | UUID NOT NULL | FK → users(id) |
| block_type | TEXT NOT NULL | paragraph \| bullet \| heading \| list_item |
| content | JSONB NOT NULL DEFAULT '{}' | structured text + metadata |
| sort_order | INT NOT NULL DEFAULT 0 | |
| embedding | vector(1536) | nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**HNSW index** on `embedding` where not null.

### fact_ledger_entries

Verified facts extracted from resume (Truth Guard source of truth).

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID NOT NULL | FK → users(id) |
| resume_version_id | UUID NOT NULL | FK → resume_versions(id) ON DELETE CASCADE |
| source_block_id | UUID | FK → resume_blocks(id), nullable |
| fact_type | TEXT NOT NULL | metric \| date \| title \| skill \| certification \| other |
| fact_text | TEXT NOT NULL | |
| is_verified | BOOLEAN NOT NULL DEFAULT false | |
| metadata | JSONB NOT NULL DEFAULT '{}' | |
| embedding | vector(1536) | nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**HNSW index** on `embedding` where not null.

### experiences

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID NOT NULL | FK → users(id) |
| resume_version_id | UUID NOT NULL | FK → resume_versions(id) ON DELETE CASCADE |
| company | TEXT NOT NULL | |
| title | TEXT NOT NULL | |
| location | TEXT | |
| start_date | DATE | |
| end_date | DATE | |
| is_current | BOOLEAN NOT NULL DEFAULT false | |
| description | TEXT | |
| bullets | JSONB NOT NULL DEFAULT '[]' | |
| sort_order | INT NOT NULL DEFAULT 0 | |
| embedding | vector(1536) | nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**HNSW index** on `embedding` where not null.

### educations

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID NOT NULL | FK → users(id) |
| resume_version_id | UUID NOT NULL | FK → resume_versions(id) ON DELETE CASCADE |
| institution | TEXT NOT NULL | |
| degree | TEXT | |
| field_of_study | TEXT | |
| start_date | DATE | |
| end_date | DATE | |
| gpa | TEXT | |
| description | TEXT | |
| sort_order | INT NOT NULL DEFAULT 0 | |
| embedding | vector(1536) | nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**HNSW index** on `embedding` where not null.

### certifications

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID NOT NULL | FK → users(id) |
| resume_version_id | UUID NOT NULL | FK → resume_versions(id) ON DELETE CASCADE |
| name | TEXT NOT NULL | |
| issuer | TEXT | |
| issue_date | DATE | |
| expiry_date | DATE | |
| credential_id | TEXT | |
| sort_order | INT NOT NULL DEFAULT 0 | |
| embedding | vector(1536) | nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**HNSW index** on `embedding` where not null.

### projects

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID NOT NULL | FK → users(id) |
| resume_version_id | UUID NOT NULL | FK → resume_versions(id) ON DELETE CASCADE |
| name | TEXT NOT NULL | |
| description | TEXT | |
| url | TEXT | |
| technologies | JSONB NOT NULL DEFAULT '[]' | |
| start_date | DATE | |
| end_date | DATE | |
| sort_order | INT NOT NULL DEFAULT 0 | |
| embedding | vector(1536) | nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**HNSW index** on `embedding` where not null.

### skills

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID NOT NULL | FK → users(id) |
| resume_version_id | UUID NOT NULL | FK → resume_versions(id) ON DELETE CASCADE |
| name | TEXT NOT NULL | |
| category | TEXT | e.g. language, framework, tool |
| proficiency | TEXT | nullable |
| sort_order | INT NOT NULL DEFAULT 0 | |
| embedding | vector(1536) | nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**HNSW index** on `embedding` where not null.

### job_descriptions

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID NOT NULL | FK → users(id) |
| title | TEXT NOT NULL | |
| company | TEXT | |
| source_url | TEXT | |
| raw_text | TEXT NOT NULL | |
| embedding | vector(1536) | nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**HNSW index** on `embedding` where not null.

### job_requirements

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID NOT NULL | FK → users(id) |
| job_description_id | UUID NOT NULL | FK → job_descriptions(id) ON DELETE CASCADE |
| requirement_text | TEXT NOT NULL | |
| requirement_type | TEXT NOT NULL | required \| preferred \| nice_to_have |
| embedding | vector(1536) | nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**HNSW index** on `embedding` where not null.

### resume_analyses

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID NOT NULL | FK → users(id) |
| resume_version_id | UUID NOT NULL | FK → resume_versions(id) ON DELETE CASCADE |
| job_description_id | UUID | FK → job_descriptions(id), nullable |
| analysis_type | TEXT NOT NULL | ats \| jd_match \| full |
| status | TEXT NOT NULL | pending \| running \| completed \| failed |
| overall_score | NUMERIC(5,2) | nullable |
| summary | JSONB NOT NULL DEFAULT '{}' | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### match_results

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID NOT NULL | FK → users(id) |
| resume_analysis_id | UUID NOT NULL | FK → resume_analyses(id) ON DELETE CASCADE |
| job_requirement_id | UUID NOT NULL | FK → job_requirements(id) ON DELETE CASCADE |
| match_score | NUMERIC(5,2) NOT NULL | |
| match_status | TEXT NOT NULL | matched \| partial \| missing |
| evidence | JSONB NOT NULL DEFAULT '{}' | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### issues

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID NOT NULL | FK → users(id) |
| resume_analysis_id | UUID NOT NULL | FK → resume_analyses(id) ON DELETE CASCADE |
| issue_type | TEXT NOT NULL | formatting \| keyword \| content \| truth \| other |
| severity | TEXT NOT NULL | low \| medium \| high \| critical |
| title | TEXT NOT NULL | |
| description | TEXT NOT NULL | |
| affected_block_id | UUID | FK → resume_blocks(id), nullable |
| metadata | JSONB NOT NULL DEFAULT '{}' | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### optimizations

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID NOT NULL | FK → users(id) |
| resume_version_id | UUID NOT NULL | FK → resume_versions(id) ON DELETE CASCADE |
| issue_id | UUID | FK → issues(id), nullable |
| optimization_type | TEXT NOT NULL | rewrite \| add \| remove \| restructure |
| status | TEXT NOT NULL | proposed \| applied \| rejected |
| original_content | JSONB NOT NULL DEFAULT '{}' | |
| proposed_content | JSONB NOT NULL DEFAULT '{}' | |
| applied_at | TIMESTAMPTZ | nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### applications

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID NOT NULL | FK → users(id) |
| resume_version_id | UUID NOT NULL | FK → resume_versions(id) |
| job_description_id | UUID | FK → job_descriptions(id), nullable |
| company | TEXT NOT NULL | |
| role_title | TEXT NOT NULL | |
| status | TEXT NOT NULL DEFAULT 'saved' | saved \| applied \| interviewing \| offer \| rejected \| withdrawn |
| applied_at | TIMESTAMPTZ | nullable |
| notes | TEXT | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### audit_log

Append-only PII access log (see §12).

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID NOT NULL | FK → users(id) — actor |
| action | TEXT NOT NULL | create \| read \| update \| delete |
| resource_type | TEXT NOT NULL | table name |
| resource_id | UUID NOT NULL | |
| metadata | JSONB NOT NULL DEFAULT '{}' | no raw PII payloads |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | same as created_at for append-only |

---

## §18 Folder Structure

```
/
├── apps/
│   ├── web/                          # Next.js + TypeScript + Tailwind
│   │   ├── src/
│   │   │   ├── app/
│   │   │   │   ├── login/
│   │   │   │   ├── signup/
│   │   │   │   └── resumes/new/
│   │   │   └── lib/
│   │   │       └── supabase/
│   │   └── package.json
│   └── api/                          # FastAPI backend
│       ├── main.py
│       ├── config.py
│       ├── dependencies/
│       │   └── auth.py
│       ├── routers/
│       ├── services/
│       │   └── parser/
│       ├── models/
│       ├── prompts/
│       ├── workers/
│       ├── tests/
│       ├── migrations/
│       └── requirements.txt
├── docs/
│   └── architecture.md
├── docker-compose.yml
└── .env.example
```
