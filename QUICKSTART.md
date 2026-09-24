# Resume ATS Analyzer - Quick Start Guide

Get the project up and running in **10 minutes**.

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Supabase account (or local Supabase)
- Anthropic API key

---

## 1. Clone & Setup

```bash
cd "d:\Amogh Wb Dev\Resume analyser"

# Backend dependencies
cd apps/api
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Frontend dependencies
cd ../web
npm install
```

---

## 2. Environment Variables

Create `apps/api/.env`:

```bash
# Supabase (get from https://supabase.com/dashboard/project/_/settings/api)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
SUPABASE_JWT_SECRET=your-jwt-secret

# Anthropic (get from https://console.anthropic.com/settings/keys)
ANTHROPIC_API_KEY=sk-ant-api03-...
ANTHROPIC_HAIKU_MODEL=claude-3-haiku-20240307
ANTHROPIC_SONNET_MODEL=claude-3-5-sonnet-20241022

# Redis
REDIS_URL=redis://localhost:6379/0

# Upload limits
MAX_UPLOAD_BYTES=10485760

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

Create `apps/web/.env.local`:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 3. Start Infrastructure

```bash
# Start Redis (in project root)
docker-compose up -d
```

---

## 4. Database Setup

### Option A: Use Supabase Cloud
1. Go to https://supabase.com/dashboard
2. Create a new project
3. Navigate to SQL Editor
4. Run each migration file in order:
   - `apps/api/migrations/001_extensions_and_functions.sql`
   - `apps/api/migrations/002_tables.sql`
   - `apps/api/migrations/003_hnsw_indexes.sql`
   - `apps/api/migrations/004_rls_policies.sql`
   - `apps/api/migrations/005_storage.sql`
   - `apps/api/migrations/006_parse_fields.sql`

### Option B: Use Local Supabase
```bash
# Install Supabase CLI
npm install -g supabase

# Init and start
supabase init
supabase start

# Link migrations
supabase db reset

# Get credentials
supabase status
```

---

## 5. Start Services

**Terminal 1 - API Server:**
```bash
cd apps/api
.venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Parse Worker:**
```bash
cd apps/api
.venv\Scripts\activate
rq worker parse --url redis://localhost:6379/0
```

**Terminal 3 - Frontend (Optional):**
```bash
cd apps/web
npm run dev
```

---

## 6. Verify Setup

Visit http://localhost:8000/health - should return:
```json
{"status": "ok"}
```

Visit http://localhost:8000/docs - should show FastAPI docs

---

## 7. Quick Test

### Upload a Resume

```bash
# Sign up
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123456!"
  }'

# Login (or use Supabase dashboard to get token)
# Copy the access_token from response

export TOKEN="your_access_token_here"

# Upload resume
curl -X POST http://localhost:8000/api/resumes \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/your/resume.pdf"

# Response:
# {
#   "resume_id": "uuid",
#   "version_id": "uuid",
#   "job_id": "uuid",
#   "status": "queued"
# }

# Poll job status
curl http://localhost:8000/api/jobs/JOB_ID \
  -H "Authorization: Bearer $TOKEN"
```

### Run ATS Analysis

```bash
# After resume is parsed (status: parsed)
curl -X POST http://localhost:8000/api/analyses \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_version_id": "VERSION_ID_FROM_ABOVE",
    "analysis_type": "ats"
  }'

# Response:
# {
#   "id": "analysis_uuid",
#   "overall_score": 78.5,
#   "summary": {
#     "category_scores": {
#       "contact": 20.0,
#       "sections": 18.0,
#       ...
#     }
#   },
#   "issue_count": 3
# }
```

### Create JD and Match

```bash
# Create job description
curl -X POST http://localhost:8000/api/job-descriptions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Backend Engineer",
    "company": "TechCorp",
    "raw_text": "We are seeking... 5+ years Python... Bachelor degree..."
  }'

# Response:
# {
#   "id": "jd_uuid",
#   "requirement_count": 10
# }

# Run JD match
curl -X POST http://localhost:8000/api/analyses \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_version_id": "VERSION_ID",
    "job_description_id": "JD_ID_FROM_ABOVE",
    "analysis_type": "jd_match"
  }'

# Response:
# {
#   "id": "analysis_uuid",
#   "overall_score": 72.3,
#   "summary": {
#     "matched": 7,
#     "partial": 2,
#     "missing": 1
#   }
# }
```

---

## 8. Run Tests

```bash
cd apps/api
pytest tests/ -v

# Specific tests
pytest tests/test_parser.py -v
pytest tests/test_scoring.py -v
pytest tests/test_file_validation.py -v
```

---

## 9. Development Tips

### Hot Reload
- API: `--reload` flag on uvicorn (already enabled)
- Frontend: Next.js hot reloads automatically
- Worker: Restart manually after code changes

### Debugging
```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use VS Code debugger with launch.json
```

### View Logs
- API: Console output from uvicorn
- Worker: Console output from rq worker
- Redis: `redis-cli monitor`
- Database: Supabase dashboard → Database → Logs

### Supabase Studio
```bash
# If using local Supabase
supabase start
# Then visit http://localhost:54323
```

---

## 10. Common Issues

### "Missing environment variables"
- Check `.env` file exists in `apps/api/`
- Verify all required vars are set
- Restart API server

### "Connection refused" to Redis
- Run `docker-compose up -d`
- Check Redis is running: `docker ps`
- Verify REDIS_URL in .env

### "Authentication failed"
- Get fresh token from Supabase dashboard
- Check token hasn't expired (1 hour default)
- Verify SUPABASE_JWT_SECRET matches

### "Parser failing"
- Check ANTHROPIC_API_KEY is valid
- Verify model name is correct
- Check worker is running: `rq info --url redis://localhost:6379/0`

### Parse job stuck in "parsing"
- Check worker logs
- Restart worker
- Verify resume file is valid PDF/DOCX

---

## Next Steps

- ✅ Read `PROJECT_STATUS.md` for complete project overview
- ✅ Check `STEP3_COMPLETE.md` for Step 3 details
- ✅ Run `examples/step3_usage_example.py` for full workflow
- ✅ Review `apps/api/services/scoring/README.md` for scoring docs
- ✅ Explore API docs at http://localhost:8000/docs

---

## Getting Help

- **Architecture**: `docs/architecture.md`
- **Master Prompt**: See `.cursor/rules/project.md`
- **Code Questions**: Check inline comments and docstrings
- **API Questions**: Visit http://localhost:8000/docs

---

**🎉 You're all set! Your Resume ATS Analyzer is running.**

Try uploading a resume and running an analysis to see it in action.
