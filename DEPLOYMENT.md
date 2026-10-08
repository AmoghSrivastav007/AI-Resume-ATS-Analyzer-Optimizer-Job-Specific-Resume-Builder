# Production Deployment Guide

Complete guide for deploying the Resume ATS Analyzer to production using Vercel (frontend) and Railway (backend).

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Initial Setup](#initial-setup)
4. [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
5. [Backend Deployment (Railway)](#backend-deployment-railway)
6. [Environment Configuration](#environment-configuration)
7. [Database Migration](#database-migration)
8. [Monitoring & Observability](#monitoring--observability)
9. [CI/CD Pipeline](#cicd-pipeline)
10. [Rollback Procedures](#rollback-procedures)
11. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

**Frontend**: Next.js App Router deployed on Vercel
- Automatic deployments from `main` branch
- Edge runtime for optimal performance
- Preview deployments for every PR

**Backend**: FastAPI deployed on Railway
- Web process (API server)
- Worker process (background jobs via RQ)
- Health checks for both processes

**Infrastructure**:
- Supabase: PostgreSQL database, authentication, storage
- Redis: Job queue (via Upstash or Railway addon)
- Sentry: Error tracking and performance monitoring
- Anthropic API: LLM inference

---

## Prerequisites

### Required Accounts

1. **GitHub Account** (for CI/CD)
2. **Vercel Account** (for frontend hosting)
3. **Railway Account** (for backend hosting)
4. **Supabase Account** (for database)
5. **Sentry Account** (for monitoring)
6. **Anthropic Account** (for LLM API)
7. **Upstash Account** (optional, for Redis)

### Required Tools

```bash
# Install Vercel CLI
npm install -g vercel

# Install Railway CLI
npm install -g @railway/cli

# Install Supabase CLI
npm install -g supabase
```

---

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/resume-analyzer.git
cd resume-analyzer
```

### 2. Create Production Branch

```bash
git checkout -b production
git push -u origin production
```

### 3. Set Up Supabase Project

1. Go to https://app.supabase.com
2. Create a new project (choose region closest to your users)
3. Note down:
   - Project URL
   - Anon/Public key
   - Service role key (keep secure!)
4. Run migrations (see [Database Migration](#database-migration))

### 4. Set Up Sentry Project

1. Go to https://sentry.io
2. Create new project → select "FastAPI" and "Next.js"
3. Note down:
   - Frontend DSN
   - Backend DSN
4. Configure source maps (optional but recommended)

### 5. Get Anthropic API Key

1. Go to https://console.anthropic.com
2. Create API key
3. Note down the key (starts with `sk-ant-`)

---

## Frontend Deployment (Vercel)

### Option 1: Automatic Deployment (Recommended)

1. **Import Project**
   - Go to https://vercel.com/new
   - Import your GitHub repository
   - Select `apps/web` as root directory

2. **Configure Build Settings**
   ```
   Framework Preset: Next.js
   Build Command: npm run build
   Output Directory: .next
   Install Command: npm install
   Root Directory: apps/web
   ```

3. **Add Environment Variables**
   
   Go to Project Settings → Environment Variables and add:
   
   ```env
   # Supabase
   NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
   
   # Backend API
   NEXT_PUBLIC_API_URL=https://your-api.railway.app
   
   # Sentry
   NEXT_PUBLIC_SENTRY_DSN=https://your-frontend-dsn@sentry.io/project-id
   NEXT_PUBLIC_SENTRY_ENVIRONMENT=production
   NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE=0.1
   NEXT_PUBLIC_SENTRY_REPLAYS_SESSION_SAMPLE_RATE=0.1
   NEXT_PUBLIC_SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE=1.0
   
   # Feature Flags
   NEXT_PUBLIC_FEATURE_JOB_MATCHING=true
   NEXT_PUBLIC_FEATURE_RESUME_OPTIMIZATION=true
   NEXT_PUBLIC_FEATURE_EXPORT_FORMATS=true
   
   # Config
   NEXT_PUBLIC_MAX_FILE_SIZE_MB=10
   NEXT_TELEMETRY_DISABLED=1
   ```

4. **Deploy**
   - Click "Deploy"
   - Wait for build to complete (~2-3 minutes)
   - Visit your deployment URL

### Option 2: CLI Deployment

```bash
cd apps/web

# Login to Vercel
vercel login

# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

---

## Backend Deployment (Railway)

### Step 1: Create Railway Project

```bash
# Login to Railway
railway login

# Initialize project
railway init

# Link to existing project (if already created on web)
# OR create new project
railway link
```

### Step 2: Add Redis Service

**Option A: Railway Redis Plugin**
```bash
railway add redis
```

**Option B: Upstash Redis**
1. Go to https://upstash.com
2. Create Redis database
3. Copy connection URL

### Step 3: Configure Environment Variables

```bash
# Set via CLI
railway variables set SUPABASE_URL=https://your-project.supabase.co
railway variables set SUPABASE_ANON_KEY=your-anon-key
railway variables set SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
railway variables set SUPABASE_JWT_SECRET=your-jwt-secret

railway variables set ANTHROPIC_API_KEY=sk-ant-your-key

railway variables set REDIS_URL=redis://default:password@host:port

railway variables set SENTRY_DSN=https://your-backend-dsn@sentry.io/project-id
railway variables set SENTRY_ENVIRONMENT=production
railway variables set SENTRY_TRACES_SAMPLE_RATE=0.1

railway variables set CORS_ORIGINS=https://your-app.vercel.app

railway variables set COST_TRACKING_ENABLED=true
```

**OR** set via Railway dashboard:
1. Go to your project → Variables
2. Add all variables from `apps/api/.env.example`

### Step 4: Configure Services

Railway automatically detects the `Procfile` which defines two services:

```
web: API server on port $PORT
worker: Background job processor
```

Verify in Railway dashboard:
- Project → Settings → Services
- Should show "web" and "worker"

### Step 5: Deploy

```bash
# Deploy current branch
railway up

# OR push to trigger automatic deployment
git push origin main
```

### Step 6: Verify Deployment

```bash
# Check deployment status
railway status

# View logs
railway logs

# Test health endpoint
curl https://your-api.railway.app/health
```

Expected response:
```json
{
  "status": "ok",
  "uptime_seconds": 123.45,
  "timestamp": "2024-03-15T10:30:00Z"
}
```

### Step 7: Configure Custom Domain (Optional)

```bash
# Add custom domain
railway domain add api.yourdomain.com
```

Then add CNAME record in your DNS:
```
CNAME api.yourdomain.com -> your-project.railway.app
```

---

## Environment Configuration

### Backend Environment Variables (`.env.example`)

See `apps/api/.env.example` for complete list. Critical variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | ✅ | Supabase project URL |
| `SUPABASE_ANON_KEY` | ✅ | Public API key |
| `SUPABASE_SERVICE_ROLE_KEY` | ✅ | Admin key (keep secure!) |
| `SUPABASE_JWT_SECRET` | ✅ | JWT signing secret |
| `ANTHROPIC_API_KEY` | ✅ | Claude API key |
| `REDIS_URL` | ✅ | Redis connection string |
| `SENTRY_DSN` | ⚠️ | Error tracking (highly recommended) |
| `CORS_ORIGINS` | ✅ | Allowed frontend origins |

### Frontend Environment Variables (`.env.example`)

See `apps/web/.env.example` for complete list. Critical variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_SUPABASE_URL` | ✅ | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | ✅ | Public API key |
| `NEXT_PUBLIC_API_URL` | ✅ | Backend API URL |
| `NEXT_PUBLIC_SENTRY_DSN` | ⚠️ | Error tracking (highly recommended) |

---

## Database Migration

### Run Migrations on Supabase

```bash
# Connect to your Supabase project
supabase link --project-ref your-project-ref

# Check current migration status
supabase db diff

# Run all migrations
for file in apps/api/migrations/*.sql; do
  supabase db execute --file "$file"
done

# Verify tables exist
supabase db execute --command "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
```

### Migrations Checklist

- [ ] `001_extensions_and_functions.sql` - Enable pgvector, create functions
- [ ] `002_tables.sql` - Create core tables (resumes, analyses, etc.)
- [ ] `003_hnsw_indexes.sql` - Create vector similarity indexes
- [ ] `004_rls_policies.sql` - Set up Row Level Security
- [ ] `005_storage.sql` - Configure storage buckets
- [ ] `006_parse_fields.sql` - Add parsed content fields
- [ ] `007_score_breakdown.sql` - Add score breakdown columns
- [ ] `008_job_postings.sql` - Create job postings table
- [ ] `009_step6_matching.sql` - Add matching features
- [ ] `010_export_jobs.sql` - Add export job tracking

### Verify Migration Success

```sql
-- Check vector extension
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Check tables
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Check RLS policies
SELECT schemaname, tablename, policyname 
FROM pg_policies 
WHERE schemaname = 'public';

-- Check storage buckets
SELECT name FROM storage.buckets;
```

---

## Monitoring & Observability

### Sentry Setup

**Backend (FastAPI)**

Sentry is automatically initialized in `apps/api/main.py`:
```python
sentry_sdk.init(
    dsn=settings.sentry_dsn,
    environment=settings.sentry_environment,
    traces_sample_rate=0.1,  # 10% of transactions
)
```

**Frontend (Next.js)**

Create `apps/web/sentry.client.config.js`:
```javascript
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NEXT_PUBLIC_SENTRY_ENVIRONMENT,
  tracesSampleRate: 0.1,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
});
```

### Health Check Endpoints

**Basic Health Check**
```bash
curl https://your-api.railway.app/health
```

Response:
```json
{
  "status": "ok",
  "uptime_seconds": 3600,
  "timestamp": "2024-03-15T10:30:00Z"
}
```

**Readiness Check** (for load balancers)
```bash
curl https://your-api.railway.app/health/ready
```

Response:
```json
{
  "ready": true,
  "checks": {
    "supabase": true,
    "redis": true
  }
}
```

### Cost Tracking Dashboard

Access LLM usage costs via API:

```bash
# Daily costs
curl https://your-api.railway.app/api/costs/daily \
  -H "Authorization: Bearer $TOKEN"

# Monthly costs
curl https://your-api.railway.app/api/costs/monthly \
  -H "Authorization: Bearer $TOKEN"

# 7-day summary
curl https://your-api.railway.app/api/costs/summary?days=7 \
  -H "Authorization: Bearer $TOKEN"

# Recent LLM calls
curl https://your-api.railway.app/api/costs/recent?limit=50 \
  -H "Authorization: Bearer $TOKEN"
```

### Log Aggregation

**Railway Logs**
```bash
# View live logs
railway logs --service web
railway logs --service worker

# Follow logs
railway logs --follow

# Filter by time
railway logs --since 1h
```

**Export Logs to External Service** (optional)

Railway supports log drains to:
- Datadog
- Logtail
- Papertrail
- Custom HTTP endpoint

Configure via: Project Settings → Observability → Log Drains

---

## CI/CD Pipeline

### GitHub Actions Workflow

The CI/CD pipeline (`.github/workflows/ci-cd.yml`) runs automatically on:
- Push to `main` branch
- Pull requests to `main`

**Pipeline Stages**:

1. **Backend Tests** (~20s)
   - Install Python dependencies
   - Run pytest suite (130 tests)
   - Generate coverage report

2. **Evaluation Tests** (~2min)
   - Run evaluation benchmark
   - Run hallucination detection
   - Fail if critical issues found

3. **Frontend Tests** (~30s)
   - Install Node.js dependencies
   - Run linter (ESLint)
   - Build Next.js app

4. **Deploy to Vercel** (~2min)
   - Triggered on main branch push
   - Automatic if all tests pass

5. **Deploy to Railway** (~3min)
   - Triggered on main branch push
   - Deploys web + worker services

6. **Post-Deployment Health Checks** (~10s)
   - Verify frontend is accessible
   - Verify backend health endpoint
   - Verify readiness checks pass

### Manual Deployment Trigger

```bash
# Trigger CI/CD manually
gh workflow run ci-cd.yml

# Check workflow status
gh run list --workflow=ci-cd.yml
```

### Deployment Approval (Optional)

To require manual approval before production deploys:

1. Go to GitHub → Settings → Environments
2. Create "production" environment
3. Add required reviewers
4. Update workflow to use `environment: production`

---

## Rollback Procedures

### Frontend Rollback (Vercel)

**Via Dashboard**:
1. Go to your project → Deployments
2. Find the last known good deployment
3. Click "..." → Promote to Production

**Via CLI**:
```bash
# List recent deployments
vercel ls

# Rollback to specific deployment
vercel rollback <deployment-url>
```

### Backend Rollback (Railway)

**Via Dashboard**:
1. Go to your project → Deployments
2. Find the last known good deployment
3. Click "Rollback to this version"

**Via CLI**:
```bash
# List deployments
railway history

# Rollback to previous deployment
railway rollback
```

**Via Git**:
```bash
# Revert to previous commit
git revert HEAD
git push origin main

# OR reset to specific commit (destructive!)
git reset --hard <commit-hash>
git push --force origin main
```

### Database Rollback

**⚠️ Warning**: Database rollbacks are risky and should be avoided if possible.

**Option 1: Restore from Backup**
```bash
# Supabase creates daily backups
# Restore via: Dashboard → Database → Backups → Restore
```

**Option 2: Reverse Migration**
```sql
-- Write reverse migration SQL
-- Example: Drop column added in latest migration
ALTER TABLE resumes DROP COLUMN IF EXISTS new_column;

-- Execute via Supabase CLI
supabase db execute --file reverse_migration.sql
```

### Emergency Procedures

**If backend is completely down**:

1. Check Railway status: https://railway.app/status
2. Check health endpoint: `curl https://your-api.railway.app/health`
3. View logs: `railway logs --service web --tail 100`
4. Restart service: `railway restart`
5. If persists, rollback deployment

**If database is unresponsive**:

1. Check Supabase status: https://status.supabase.com
2. Check connection pooler: Dashboard → Database → Connection Pooler
3. Check active connections: Dashboard → Database → Query Performance
4. If overloaded, increase connection limit (Settings → Database)

**If costs spike unexpectedly**:

1. Check cost dashboard: `/api/costs/summary?days=1`
2. Identify task type causing spike
3. Temporarily disable feature:
   ```bash
   # Via Railway CLI
   railway variables set FEATURE_RESUME_OPTIMIZATION=false
   railway restart
   ```
4. Investigate and fix root cause
5. Re-enable feature

---

## Troubleshooting

### Common Issues

#### 1. CORS Errors

**Symptom**: Frontend cannot connect to backend, browser console shows CORS error

**Solution**:
```bash
# Check CORS_ORIGINS is set correctly on Railway
railway variables get CORS_ORIGINS

# Should be your Vercel domain (or multiple domains comma-separated)
railway variables set CORS_ORIGINS=https://your-app.vercel.app,https://your-app-preview.vercel.app
railway restart
```

#### 2. Authentication Errors

**Symptom**: "Invalid JWT token" or "Unauthorized" errors

**Solution**:
```bash
# Verify JWT secret matches between Supabase and backend
supabase secrets list

# On Railway, update JWT secret
railway variables set SUPABASE_JWT_SECRET=your-jwt-secret
railway restart
```

#### 3. High Latency

**Symptom**: Slow API responses (>1s)

**Diagnosis**:
```bash
# Check response times via headers
curl -w "@curl-format.txt" https://your-api.railway.app/health

# Check Sentry performance monitoring
# Dashboard → Performance → Web Vitals
```

**Solutions**:
- Increase Railway plan (more CPU/memory)
- Add database indexes (check slow query log in Supabase)
- Enable Redis caching for frequently accessed data
- Move to same region as Supabase

#### 4. Worker Not Processing Jobs

**Symptom**: Background jobs stuck in queue

**Diagnosis**:
```bash
# Check worker logs
railway logs --service worker

# Check Redis queue length
redis-cli -u $REDIS_URL llen rq:queue:default
```

**Solutions**:
```bash
# Restart worker
railway restart --service worker

# Increase worker instances (Railway dashboard)
# Project → Settings → Services → worker → Scale

# Check for crashed jobs
railway run rq info --url $REDIS_URL
```

#### 5. Out of Memory Errors

**Symptom**: 502 Bad Gateway, logs show "killed" or OOM errors

**Solutions**:
- Upgrade Railway plan (more RAM)
- Reduce concurrent workers in RQ
- Add pagination to large queries
- Stream large file operations instead of loading into memory

#### 6. Rate Limiting Issues

**Symptom**: 429 Too Many Requests errors

**Solution**:
```bash
# Adjust rate limits in backend config
railway variables set RATE_LIMIT_RESUME_UPLOAD=10
railway variables set RATE_LIMIT_WINDOW_MINUTES=60
railway restart
```

---

## Cost Estimation

### Monthly Costs (MVP/Low Traffic)

| Service | Plan | Cost |
|---------|------|------|
| Vercel | Hobby | $0 |
| Railway | Starter | $5/service × 2 = $10 |
| Supabase | Free | $0 (up to 500MB DB) |
| Upstash Redis | Free | $0 (up to 10k commands/day) |
| Sentry | Developer | $0 (up to 5k errors/month) |
| Anthropic API | Pay-as-go | ~$20-50/month |
| **Total** | | **~$30-60/month** |

### Scaling Costs (Medium Traffic)

| Service | Plan | Cost |
|---------|------|------|
| Vercel | Pro | $20 |
| Railway | Developer | $10/service × 2 = $20 |
| Supabase | Pro | $25 |
| Upstash Redis | Pay-as-go | ~$10 |
| Sentry | Team | $26 |
| Anthropic API | Pay-as-go | ~$100-200/month |
| **Total** | | **~$200-300/month** |

---

## Security Checklist

- [ ] All secrets stored in environment variables (never in code)
- [ ] Service role key only used server-side (never exposed to client)
- [ ] CORS configured with specific origins (not `*`)
- [ ] Rate limiting enabled on all endpoints
- [ ] RLS policies enabled on all Supabase tables
- [ ] File upload validation (size, type, virus scanning)
- [ ] Input sanitization on all user inputs
- [ ] HTTPS enforced (automatic on Vercel/Railway)
- [ ] Sentry configured to exclude PII from error reports
- [ ] Database backups enabled (automatic on Supabase)
- [ ] API keys rotated regularly (every 90 days)
- [ ] Monitoring alerts configured (Sentry, Railway)

---

## Support & Resources

**Documentation**:
- [Vercel Docs](https://vercel.com/docs)
- [Railway Docs](https://docs.railway.app)
- [Supabase Docs](https://supabase.com/docs)
- [Sentry Docs](https://docs.sentry.io)

**Status Pages**:
- [Vercel Status](https://www.vercel-status.com)
- [Railway Status](https://railway.app/status)
- [Supabase Status](https://status.supabase.com)
- [Anthropic Status](https://status.anthropic.com)

**Community**:
- [Railway Discord](https://discord.gg/railway)
- [Supabase Discord](https://discord.supabase.com)

---

## Post-Deployment Checklist

After successful deployment, verify:

- [ ] Frontend loads at production URL
- [ ] Can create account / login via Supabase Auth
- [ ] Can upload resume PDF
- [ ] Resume parsing completes successfully
- [ ] Can view analysis results
- [ ] Health check returns 200 OK
- [ ] Sentry receiving error reports (test by triggering intentional error)
- [ ] Cost tracking logging LLM calls
- [ ] Background worker processing jobs
- [ ] Email notifications working (if configured)
- [ ] All CRUD operations functional
- [ ] Mobile responsive design working
- [ ] Cross-browser compatibility (Chrome, Firefox, Safari)

---

**Last Updated**: 2024-03-15  
**Version**: 1.0.0  
**Maintained By**: Engineering Team
