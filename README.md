# Resume ATS Analyzer & Optimizer

Monorepo for resume upload, ATS analysis, and JD matching.

## Stack

- **apps/web** — Next.js (App Router) + TypeScript + Tailwind
- **apps/api** — FastAPI + Supabase
- **Postgres + pgvector**, **Redis** — via Docker Compose (local) or Supabase (cloud)

## Quick start (Step 1)

### 1. Supabase project

1. Create a project at [supabase.com](https://supabase.com).
2. In the SQL Editor, run migrations in order:
   - `apps/api/migrations/001_extensions_and_functions.sql`
   - `apps/api/migrations/002_tables.sql`
   - `apps/api/migrations/003_hnsw_indexes.sql`
   - `apps/api/migrations/004_rls_policies.sql`
   - `apps/api/migrations/005_storage.sql`
   - `apps/api/migrations/006_parse_fields.sql`
3. Copy Project URL, anon key, service role key, and JWT secret from **Settings → API**.

### 2. Environment

```powershell
copy .env.example .env
copy .env.example apps\api\.env
copy .env.example apps\web\.env.local
```

Fill in your Supabase credentials in all three files.

### 3. Local services

```powershell
docker compose up -d
```

### 4. Backend

```powershell
cd apps\api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

In a second terminal, start the parse worker:

```powershell
cd apps\api
.\.venv\Scripts\Activate.ps1
python -m workers.parse_worker
```

### 5. Frontend

```powershell
cd apps\web
npm run dev
```

Open http://localhost:3000 → sign up → upload a PDF or DOCX at `/resumes/new`.

## Definition of done (Step 2)

- Upload a text-based PDF/DOCX → parse job runs → `resume_sections`, `resume_blocks`, and `fact_ledger_entries` are populated
- `GET /api/resumes/:id` returns ordered sections/blocks; `GET /api/jobs/:id` reports parse status
- A scanned/image-only PDF is flagged `needs_ocr` with: "This looks like a scanned resume. OCR support is coming soon — please upload a text-based PDF or DOCX."
