# Deployment Quick Start 🚀

**TL;DR**: Get your Resume ATS Analyzer deployed to production in 2 hours.

For complete details, see [DEPLOYMENT.md](./DEPLOYMENT.md)

---

## Prerequisites Checklist

- [ ] GitHub account (for CI/CD)
- [ ] Vercel account (frontend hosting)
- [ ] Railway account (backend hosting)
- [ ] Supabase account (database)
- [ ] Sentry account (monitoring)
- [ ] Anthropic API key (LLM inference)

**Time**: 30 minutes to create all accounts

---

## Step 1: Set Up Supabase (15 min)

```bash
# 1. Create project at https://app.supabase.com
# 2. Note your credentials:
#    - Project URL
#    - Anon key
#    - Service role key
#    - JWT secret

# 3. Run migrations
cd apps/api/migrations

# Execute each SQL file in Supabase SQL Editor:
# 001_extensions_and_functions.sql
# 002_tables.sql
# 003_hnsw_indexes.sql
# 004_rls_policies.sql
# 005_storage.sql
# 006_parse_fields.sql
# 007_score_breakdown.sql
# 008_job_postings.sql
# 009_step6_matching.sql
# 010_export_jobs.sql

# 4. Verify tables exist
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
```

---

## Step 2: Set Up Sentry (5 min)

```bash
# 1. Create two projects at https://sentry.io
#    - "resume-analyzer-frontend" (Next.js)
#    - "resume-analyzer-backend" (FastAPI)

# 2. Copy DSN from each project:
#    Settings → Client Keys (DSN)
```

---

## Step 3: Deploy Backend to Railway (20 min)

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login and create project
railway login
railway init

# 3. Add Redis service
railway add redis

# 4. Set environment variables (use Railway dashboard or CLI)
railway variables set SUPABASE_URL=https://xxxxx.supabase.co
railway variables set SUPABASE_ANON_KEY=eyJhbGc...
railway variables set SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
railway variables set SUPABASE_JWT_SECRET=your-jwt-secret

railway variables set ANTHROPIC_API_KEY=sk-ant-xxxxx
railway variables set ANTHROPIC_HAIKU_MODEL=claude-3-haiku-20240307

railway variables set REDIS_URL=${{Redis.REDIS_URL}}

railway variables set SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
railway variables set SENTRY_ENVIRONMENT=production

railway variables set CORS_ORIGINS=https://your-app.vercel.app

railway variables set COST_TRACKING_ENABLED=true

# 5. Deploy
git push

# 6. Verify deployment
railway status
curl https://your-project.railway.app/health
```

Expected response:
```json
{"status": "ok", "uptime_seconds": 10.5, "timestamp": "2024-03-15T10:30:00Z"}
```

---

## Step 4: Deploy Frontend to Vercel (15 min)

```bash
# Option A: Via Dashboard (Recommended)
# 1. Go to https://vercel.com/new
# 2. Import your GitHub repository
# 3. Set root directory: apps/web
# 4. Add environment variables (see below)
# 5. Click Deploy

# Option B: Via CLI
npm install -g vercel
cd apps/web
vercel login
vercel --prod
```

### Frontend Environment Variables (Vercel Dashboard)

```env
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...

# Backend API (your Railway URL)
NEXT_PUBLIC_API_URL=https://your-project.railway.app

# Sentry
NEXT_PUBLIC_SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
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

---

## Step 5: Configure CI/CD (10 min)

### GitHub Secrets

Go to: Repository → Settings → Secrets and variables → Actions

Add these secrets:

```
# Vercel
VERCEL_TOKEN          # Get from: vercel login && vercel token create
VERCEL_ORG_ID         # Get from: .vercel/project.json
VERCEL_PROJECT_ID     # Get from: .vercel/project.json

# Railway  
RAILWAY_TOKEN         # Get from: railway token create
```

### Test CI/CD

```bash
# Push to main to trigger deployment
git add .
git commit -m "Initial production deployment"
git push origin main

# Watch deployment
gh run watch
```

---

## Step 6: Verify Deployment (10 min)

### Health Checks

```bash
# Backend health
curl https://your-project.railway.app/health

# Backend readiness
curl https://your-project.railway.app/health/ready

# Frontend (should load in browser)
open https://your-app.vercel.app
```

### Functional Test

1. Visit your frontend URL
2. Create account (Supabase Auth)
3. Upload a test resume PDF
4. Verify parsing completes
5. View analysis results

### Cost Tracking

```bash
# Get JWT token from browser (login and inspect localStorage)
TOKEN="your-jwt-token"

# Check costs are being tracked
curl https://your-project.railway.app/api/costs/recent \
  -H "Authorization: Bearer $TOKEN"
```

### Sentry

1. Trigger test error:
   - Backend: Throw exception in API
   - Frontend: Click broken button
2. Check Sentry dashboard: https://sentry.io
3. Verify errors appear

---

## Step 7: Update CORS (5 min)

After you have your Vercel URL:

```bash
# Update Railway with correct CORS origins
railway variables set CORS_ORIGINS=https://your-app.vercel.app

# Restart backend
railway restart
```

---

## Post-Deployment Checklist

- [ ] Frontend loads at Vercel URL
- [ ] Backend health check returns 200
- [ ] Can create account / login
- [ ] Can upload resume
- [ ] Resume parsing works
- [ ] Analysis results display
- [ ] Sentry receiving events
- [ ] Cost tracking working
- [ ] CI/CD pipeline passing
- [ ] No CORS errors in browser console

---

## Monitoring URLs

**Frontend**: https://your-app.vercel.app  
**Backend**: https://your-project.railway.app  
**Backend Health**: https://your-project.railway.app/health  
**Sentry**: https://sentry.io  
**Vercel Dashboard**: https://vercel.com/dashboard  
**Railway Dashboard**: https://railway.app/dashboard  
**Supabase Dashboard**: https://app.supabase.com  
**GitHub Actions**: https://github.com/your-org/resume-analyzer/actions

---

## Common Issues

### CORS Errors

**Problem**: Browser shows CORS error  
**Solution**: Update `CORS_ORIGINS` on Railway to include your Vercel domain

```bash
railway variables set CORS_ORIGINS=https://your-app.vercel.app
railway restart
```

### Authentication Not Working

**Problem**: "Invalid JWT token"  
**Solution**: Verify `SUPABASE_JWT_SECRET` matches in both Supabase and Railway

### Worker Not Processing Jobs

**Problem**: Background jobs stuck  
**Solution**: Check worker service logs

```bash
railway logs --service worker
railway restart --service worker
```

### High Costs

**Problem**: Anthropic costs higher than expected  
**Solution**: Check cost dashboard

```bash
curl https://your-project.railway.app/api/costs/summary?days=7 \
  -H "Authorization: Bearer $TOKEN"
```

---

## Rollback

### Frontend (Vercel)

```bash
# Via dashboard: Deployments → Select previous → Promote to Production

# Via CLI
vercel rollback <deployment-url>
```

### Backend (Railway)

```bash
# Via dashboard: Deployments → Select previous → Rollback

# Via CLI
railway rollback
```

---

## Cost Estimate

**Monthly Production Costs (Low Traffic)**:

| Service | Cost |
|---------|------|
| Vercel | $0 (Hobby) |
| Railway | $10 (2 services) |
| Supabase | $0 (Free tier) |
| Redis | $0 (Railway addon) |
| Sentry | $0 (Developer tier) |
| Anthropic | $20-50 (usage) |
| **Total** | **$30-60/month** |

---

## Support

**Full Documentation**: [DEPLOYMENT.md](./DEPLOYMENT.md) (600+ lines)  
**CI/CD Guide**: [.github/workflows/README.md](./.github/workflows/README.md)  
**Backend Config**: [apps/api/.env.example](./apps/api/.env.example)  
**Frontend Config**: [apps/web/.env.example](./apps/web/.env.example)

**Questions?** Check troubleshooting section in DEPLOYMENT.md

---

**Total Time**: ~2 hours for first deployment  
**Subsequent Deploys**: <5 minutes (automatic on git push)

🎉 **You're live!**
