# Production Environment Variables Configuration

**For**: MVP Deployment to Vercel + Railway  
**Date**: October 8, 2026

---

## Overview

This document contains all environment variables needed for production deployment.

**⚠️ SECURITY WARNING**: Never commit actual values to git. Use this as a reference only.

---

## Frontend Environment Variables (Vercel)

### Navigate To
Vercel Dashboard → Your Project → Settings → Environment Variables

### Required Variables (4)

#### 1. NEXT_PUBLIC_API_URL
**Description**: Backend API URL  
**Example**: `https://your-backend.up.railway.app`  
**Where to get**: Railway dashboard after backend deployment  
**Environments**: Production, Preview, Development

```
Key: NEXT_PUBLIC_API_URL
Value: https://your-backend-name.up.railway.app
```

---

#### 2. NEXT_PUBLIC_SUPABASE_URL
**Description**: Supabase project URL  
**Example**: `https://abcdefghijklmn.supabase.co`  
**Where to get**: Supabase Dashboard → Settings → API  
**Environments**: Production, Preview, Development

```
Key: NEXT_PUBLIC_SUPABASE_URL
Value: https://your-project-id.supabase.co
```

---

#### 3. NEXT_PUBLIC_SUPABASE_ANON_KEY
**Description**: Supabase anonymous/public key  
**Example**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`  
**Where to get**: Supabase Dashboard → Settings → API → anon/public key  
**Environments**: Production, Preview, Development  
**Note**: This is safe to expose in frontend (it's called "anon" key)

```
Key: NEXT_PUBLIC_SUPABASE_ANON_KEY
Value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your-anon-key-here...
```

---

#### 4. NEXT_PUBLIC_SENTRY_DSN (Optional but Recommended)
**Description**: Sentry error tracking DSN for frontend  
**Example**: `https://abc123@o123456.ingest.sentry.io/123456`  
**Where to get**: Sentry Dashboard → Settings → Projects → Your Frontend Project → Client Keys (DSN)  
**Environments**: Production, Preview, Development

```
Key: NEXT_PUBLIC_SENTRY_DSN
Value: https://your-key@your-org.ingest.sentry.io/project-id
```

---

### How to Add in Vercel

1. Go to https://vercel.com/dashboard
2. Select your project
3. Click "Settings" tab
4. Click "Environment Variables" in sidebar
5. For each variable:
   - Enter Key name (e.g., `NEXT_PUBLIC_API_URL`)
   - Enter Value
   - Select all environments: ✅ Production ✅ Preview ✅ Development
   - Click "Save"
6. After adding all 4, trigger a redeploy

---

## Backend Environment Variables (Railway)

### Navigate To
Railway Dashboard → Your Project → Backend Service → Variables Tab

### Required Variables (8-10)

#### 1. SUPABASE_URL
**Description**: Supabase project URL (same as frontend)  
**Example**: `https://abcdefghijklmn.supabase.co`  
**Where to get**: Supabase Dashboard → Settings → API

```
Key: SUPABASE_URL
Value: https://your-project-id.supabase.co
```

---

#### 2. SUPABASE_KEY
**Description**: Supabase SERVICE ROLE key (NOT anon key)  
**Example**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (different from anon key)  
**Where to get**: Supabase Dashboard → Settings → API → service_role key  
**⚠️ SECURITY**: Keep this secret! Has full database access, bypasses RLS

```
Key: SUPABASE_KEY
Value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your-service-role-key...
```

---

#### 3. SUPABASE_JWT_SECRET
**Description**: JWT secret for token verification  
**Example**: `your-super-secret-jwt-secret-here-min-32-chars`  
**Where to get**: Supabase Dashboard → Settings → API → JWT Secret  
**⚠️ SECURITY**: Keep this secret! Used to verify JWT tokens

```
Key: SUPABASE_JWT_SECRET
Value: your-jwt-secret-at-least-32-characters-long
```

---

#### 4. ANTHROPIC_API_KEY
**Description**: Claude API key for LLM operations  
**Example**: `sk-ant-api03-...`  
**Where to get**: https://console.anthropic.com/settings/keys  
**⚠️ SECURITY**: Keep this secret! Costs money if exposed  
**Note**: Need to add payment method in Anthropic console

```
Key: ANTHROPIC_API_KEY
Value: sk-ant-api03-your-key-here...
```

---

#### 5. REDIS_URL
**Description**: Redis connection string for cost tracking  
**Example**: `redis://default:password@host:6379`  
**Where to get**: Railway auto-provisions this when you add Redis service  
**Note**: Usually auto-populated by Railway - verify it exists

```
Key: REDIS_URL
Value: redis://default:password@redis.railway.internal:6379
```

**How to add Redis in Railway**:
1. In your Railway project, click "+ New"
2. Select "Database" → "Redis"
3. REDIS_URL will be auto-added to all services

---

#### 6. COST_TRACKING_ENABLED
**Description**: Enable LLM cost tracking  
**Example**: `true`  
**Where to get**: Set manually  
**Options**: `true` or `false`

```
Key: COST_TRACKING_ENABLED
Value: true
```

---

#### 7. ALLOWED_ORIGINS
**Description**: CORS allowed origins (frontend URLs)  
**Example**: `https://your-app.vercel.app,https://your-app-*.vercel.app`  
**Where to get**: Your Vercel deployment URLs  
**Note**: Include both production and preview domains

```
Key: ALLOWED_ORIGINS
Value: https://your-app.vercel.app,https://your-app-*.vercel.app,https://*.vercel.app
```

**Important**: Update this after first Vercel deployment with actual URL

---

#### 8. MAX_FILE_SIZE_MB
**Description**: Maximum resume upload size in MB  
**Example**: `10`  
**Where to get**: Set manually  
**Recommended**: 10 MB for resumes

```
Key: MAX_FILE_SIZE_MB
Value: 10
```

---

#### 9. SENTRY_DSN (Optional but Recommended)
**Description**: Sentry error tracking DSN for backend  
**Example**: `https://abc123@o123456.ingest.sentry.io/789012`  
**Where to get**: Sentry Dashboard → Backend Project → Client Keys (DSN)

```
Key: SENTRY_DSN
Value: https://your-key@your-org.ingest.sentry.io/backend-project-id
```

---

#### 10. PYTHON_VERSION (Optional)
**Description**: Python version for Railway  
**Example**: `3.11`  
**Where to get**: Set manually  
**Note**: Railway auto-detects, but explicit is better

```
Key: PYTHON_VERSION
Value: 3.11
```

---

### How to Add in Railway

1. Go to https://railway.app/dashboard
2. Select your project
3. Click on your backend service
4. Click "Variables" tab
5. Click "+ New Variable"
6. For each variable:
   - Enter Variable name
   - Enter Value
   - Click "Add"
7. Click "Deploy" to apply changes

---

## Supabase Configuration

### Required Setup in Supabase

#### 1. Enable Required Extensions
Navigate to: Supabase Dashboard → Database → Extensions

Enable these extensions:
- ✅ `vector` (pgvector for embeddings)
- ✅ `pg_trgm` (for text search)
- ✅ `uuid-ossp` (for UUID generation)

#### 2. Run Migrations
All SQL migrations are in `apps/api/migrations/`:
- `001_extensions_and_functions.sql`
- `002_tables.sql`
- `003_hnsw_indexes.sql`
- `004_rls_policies.sql`
- `005_storage.sql`
- `006_parse_fields.sql`
- `007_score_breakdown.sql`
- `008_job_postings.sql`
- `009_step6_matching.sql`
- `010_export_jobs.sql`

**Run via**:
- Supabase Dashboard → SQL Editor → New Query → Paste → Run
- Or use `psql` with connection string
- Or Railway CLI after deployment

#### 3. Configure Storage Bucket
Navigate to: Supabase Dashboard → Storage

Create bucket:
- Name: `resumes`
- Public: ❌ No (private)
- Allowed MIME types: `application/pdf`, `application/msword`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- Max file size: 10 MB

#### 4. Verify RLS Policies
Navigate to: Supabase Dashboard → Authentication → Policies

Verify tables have RLS enabled:
- ✅ `resumes` - Users can only access their own
- ✅ `resume_versions` - Users can only access their own
- ✅ `resume_blocks` - Users can only access their own
- ✅ `job_postings` - Users can only access their own
- ✅ All other tables with user_id column

---

## Sentry Configuration

### Frontend Project (Next.js)

1. Go to https://sentry.io
2. Create organization (or use existing)
3. Click "Create Project"
4. Select platform: **Next.js**
5. Name: `resume-analyzer-frontend`
6. Copy the DSN (looks like: `https://...@sentry.io/...`)
7. Add to Vercel environment variables

### Backend Project (Python)

1. In same Sentry organization
2. Click "Create Project"
3. Select platform: **Python** or **FastAPI**
4. Name: `resume-analyzer-backend`
5. Copy the DSN
6. Add to Railway environment variables

### Configure Alerts (Optional)

Navigate to: Sentry Project → Settings → Alerts

Recommended alerts:
- Error rate > 10 errors/hour
- New issue appears
- Regression (previously resolved issue returns)

---

## Verification Checklist

### Before Deploying Backend
- [ ] SUPABASE_URL set correctly
- [ ] SUPABASE_KEY is SERVICE ROLE key (not anon)
- [ ] SUPABASE_JWT_SECRET matches Supabase
- [ ] ANTHROPIC_API_KEY is valid and has credits
- [ ] REDIS_URL is auto-populated (check after adding Redis)
- [ ] COST_TRACKING_ENABLED set to true
- [ ] ALLOWED_ORIGINS includes Vercel URL
- [ ] MAX_FILE_SIZE_MB set to 10

### Before Deploying Frontend
- [ ] NEXT_PUBLIC_API_URL points to Railway backend
- [ ] NEXT_PUBLIC_SUPABASE_URL matches backend
- [ ] NEXT_PUBLIC_SUPABASE_ANON_KEY is correct (anon, not service)
- [ ] NEXT_PUBLIC_SENTRY_DSN is for frontend project

### After First Deploy
- [ ] Update ALLOWED_ORIGINS in Railway with actual Vercel URL
- [ ] Test CORS by making API call from frontend
- [ ] Verify Sentry receiving errors (trigger test error)
- [ ] Check Redis connection in Railway logs
- [ ] Verify Supabase RLS policies working

---

## Common Issues and Solutions

### Issue: CORS errors in browser
**Solution**: Update ALLOWED_ORIGINS in Railway to include your exact Vercel URL

### Issue: "Invalid JWT" errors
**Solution**: Verify SUPABASE_JWT_SECRET matches Supabase exactly (no extra spaces)

### Issue: File uploads fail
**Solution**: Check Supabase storage bucket exists and is named "resumes"

### Issue: LLM calls fail
**Solution**: Verify ANTHROPIC_API_KEY is valid and has credits

### Issue: Cost tracking shows no data
**Solution**: 
1. Check REDIS_URL is set
2. Check COST_TRACKING_ENABLED=true
3. Verify Redis service running in Railway

### Issue: "Database connection failed"
**Solution**: Verify SUPABASE_URL and SUPABASE_KEY are correct

---

## Security Best Practices

### ✅ DO:
- Use service role key ONLY in backend
- Use anon key in frontend
- Keep JWT secret secure
- Rotate keys periodically
- Use environment variables for all secrets
- Enable RLS in Supabase
- Limit CORS origins to specific domains
- Monitor Sentry for leaked credentials

### ❌ DON'T:
- Never commit .env files to git
- Never expose service role key in frontend
- Never use same key for dev and prod
- Never disable RLS policies
- Never use wildcard (*) in CORS origins in production
- Never share API keys in screenshots/logs

---

## Quick Reference Card

**Print this and keep it handy during deployment**

```
┌─────────────────────────────────────────────────────────┐
│ PRODUCTION DEPLOYMENT - QUICK REFERENCE                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ VERCEL (Frontend) - 4 Variables:                        │
│  1. NEXT_PUBLIC_API_URL          (Railway URL)          │
│  2. NEXT_PUBLIC_SUPABASE_URL     (Supabase URL)         │
│  3. NEXT_PUBLIC_SUPABASE_ANON_KEY (Anon key)            │
│  4. NEXT_PUBLIC_SENTRY_DSN       (Frontend DSN)         │
│                                                          │
│ RAILWAY (Backend) - 8 Variables:                        │
│  1. SUPABASE_URL                 (Same as frontend)     │
│  2. SUPABASE_KEY                 (SERVICE ROLE key)     │
│  3. SUPABASE_JWT_SECRET          (From Supabase)        │
│  4. ANTHROPIC_API_KEY            (Claude API)           │
│  5. REDIS_URL                    (Auto-provisioned)     │
│  6. COST_TRACKING_ENABLED        (true)                 │
│  7. ALLOWED_ORIGINS              (Vercel URL)           │
│  8. MAX_FILE_SIZE_MB             (10)                   │
│                                                          │
│ SUPABASE:                                                │
│  - Enable vector extension                              │
│  - Run all 10 migrations                                │
│  - Create "resumes" storage bucket                      │
│  - Verify RLS policies active                           │
│                                                          │
│ SENTRY:                                                  │
│  - Create frontend project (Next.js)                    │
│  - Create backend project (Python)                      │
│  - Copy both DSNs                                       │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Next Steps

After configuring all environment variables:

1. ✅ Deploy backend to Railway
2. ✅ Deploy frontend to Vercel
3. ✅ Update ALLOWED_ORIGINS with actual Vercel URL
4. ✅ Test end-to-end flow
5. ✅ Verify Sentry receiving events
6. ✅ Check cost tracking dashboard

See `DEPLOYMENT_CHECKLIST.md` for detailed deployment steps.

---

**Document Version**: 1.0  
**Last Updated**: October 8, 2026  
**Status**: Ready for production deployment
