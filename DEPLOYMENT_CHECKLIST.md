# Production Deployment Checklist

**Date**: October 8, 2026  
**MVP Version**: 1.0.0  
**Deployment Target**: Vercel (Frontend) + Railway (Backend)  

---

## Pre-Deployment Checklist

### Code Quality ✅
- [x] All TypeScript files compile without errors
- [x] No ESLint warnings (critical only)
- [x] All pages tested at 5 breakpoints
- [x] Dark mode works across all pages
- [x] No console errors in production build

### Environment Variables

#### Frontend (.env.local → Vercel)
```bash
NEXT_PUBLIC_API_URL=https://api.your-domain.com
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
NEXT_PUBLIC_SENTRY_DSN=your_frontend_sentry_dsn
```

#### Backend (.env → Railway)
```bash
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_service_role_key
SUPABASE_JWT_SECRET=your_jwt_secret

# Redis (Railway will auto-provision)
REDIS_URL=redis://default:password@host:port

# Anthropic AI
ANTHROPIC_API_KEY=your_anthropic_key

# Cost Tracking
COST_TRACKING_ENABLED=true

# Sentry
SENTRY_DSN=your_backend_sentry_dsn

# CORS (Vercel URL)
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app

# File Storage
MAX_FILE_SIZE_MB=10
```

### Dependencies Check
- [x] package.json: All dependencies locked
- [x] requirements.txt: All Python packages pinned
- [x] No dev dependencies in production
- [x] Recharts installed successfully

---

## Task 5: Account Setup (30 minutes)

### Step 5.1: Vercel Account ⏳
**Actions**:
1. [ ] Sign up at https://vercel.com/signup
2. [ ] Connect GitHub account
3. [ ] Import repository
4. [ ] Configure root directory: `apps/web`
5. [ ] Note project ID

**Verification**:
- [ ] Dashboard accessible
- [ ] GitHub integration active
- [ ] Deployment webhook configured

**Expected First Deploy**: ❌ FAIL (missing env vars - this is normal)

---

### Step 5.2: Railway Account ⏳
**Actions**:
1. [ ] Sign up at https://railway.app/login
2. [ ] Connect GitHub account
3. [ ] Create new project from repo
4. [ ] Railway auto-detects: FastAPI + Redis

**Services Created**:
- [ ] Web service (FastAPI)
- [ ] Redis service (auto-provisioned)
- [ ] Note: Railway provides REDIS_URL automatically

**Verification**:
- [ ] Project dashboard accessible
- [ ] Services detected correctly
- [ ] Redis addon connected

---

### Step 5.3: Sentry Account ⏳
**Actions**:
1. [ ] Sign up at https://sentry.io/signup
2. [ ] Create organization: "Resume Analyzer"
3. [ ] Create project: "frontend" (Next.js platform)
4. [ ] Copy frontend DSN
5. [ ] Create project: "backend" (Python platform)
6. [ ] Copy backend DSN

**Verification**:
- [ ] Both projects created
- [ ] DSNs copied to secure location
- [ ] Test events can be sent

---

## Task 6: Configure Environment Variables (15 minutes)

### Step 6.1: Vercel Environment Variables
**Navigate**: Vercel Dashboard → Project → Settings → Environment Variables

**Variables to Add**:
```
NEXT_PUBLIC_API_URL=https://your-railway-backend.up.railway.app
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxx...
NEXT_PUBLIC_SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
```

**Environment**: Production, Preview, Development (all 3)

**Verification**:
- [ ] All 4 variables added
- [ ] Applied to all environments
- [ ] No typos in URLs

---

### Step 6.2: Railway Environment Variables
**Navigate**: Railway Dashboard → Project → Web Service → Variables

**Variables to Add**:
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_service_role_key
SUPABASE_JWT_SECRET=your_jwt_secret
ANTHROPIC_API_KEY=sk-ant-xxx
COST_TRACKING_ENABLED=true
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
ALLOWED_ORIGINS=https://your-app.vercel.app,https://your-app-*.vercel.app
MAX_FILE_SIZE_MB=10
```

**Note**: REDIS_URL is auto-provided by Railway

**Verification**:
- [ ] All 8 variables added
- [ ] REDIS_URL auto-populated
- [ ] Sensitive values hidden

---

## Task 7: Deploy Backend (20 minutes)

### Step 7.1: Railway Initial Deploy
**Action**: Push to main branch (auto-deploys)

```bash
git add .
git commit -m "chore: prepare for production deployment"
git push origin main
```

**Monitor**: Railway Dashboard → Deployments

**Expected Build Time**: 3-5 minutes

**Verification**:
- [ ] Build succeeds
- [ ] Health check passes
- [ ] Service URL accessible
- [ ] GET /health returns 200

---

### Step 7.2: Run Database Migrations
**Method**: Railway CLI or SSH

```bash
# Option 1: Railway CLI
railway run python migrate.py

# Option 2: Add to Procfile
release: python migrate.py
```

**Verification**:
- [ ] All 10 migrations run successfully
- [ ] Supabase tables created
- [ ] Indexes created
- [ ] RLS policies active

---

### Step 7.3: Test Backend Endpoints
**Test URLs**:
```bash
# Health check
curl https://your-backend.up.railway.app/health

# API docs
curl https://your-backend.up.railway.app/docs

# Cost endpoint (should return 401 without auth)
curl https://your-backend.up.railway.app/api/costs/summary
```

**Verification**:
- [ ] /health returns {"status": "ok"}
- [ ] /docs loads Swagger UI
- [ ] CORS headers present
- [ ] 401 for protected endpoints

---

## Task 8: Deploy Frontend (20 minutes)

### Step 8.1: Update API URL
**File**: `apps/web/.env.local`

```bash
# Replace localhost with Railway URL
NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app
```

**Commit**:
```bash
git add apps/web/.env.local
git commit -m "feat: configure production API URL"
git push origin main
```

**Verification**:
- [ ] Env var updated in Vercel
- [ ] Points to Railway backend

---

### Step 8.2: Vercel Deploy
**Action**: Push triggers auto-deploy

**Monitor**: Vercel Dashboard → Deployments

**Expected Build Time**: 2-4 minutes

**Build Steps**:
1. Install dependencies
2. Run Next.js build
3. Generate static pages
4. Deploy to edge network

**Verification**:
- [ ] Build succeeds
- [ ] No TypeScript errors
- [ ] Pages pre-rendered
- [ ] Deployment URL provided

---

### Step 8.3: Test Frontend
**Test URLs**:
```
https://your-app.vercel.app/
https://your-app.vercel.app/resumes
https://your-app.vercel.app/admin/costs
```

**Checks**:
- [ ] Home page loads
- [ ] Can login with Supabase
- [ ] Can upload resume
- [ ] Can view analysis
- [ ] Can access optimization page
- [ ] Can access matching page
- [ ] Cost dashboard loads (admin only)

---

## Task 9: Post-Deployment Verification (10 minutes)

### Smoke Test Suite

#### Test 1: End-to-End Resume Flow
1. [ ] Sign up / Login
2. [ ] Upload resume (PDF)
3. [ ] Wait for parsing
4. [ ] View analysis page
5. [ ] Check quality score
6. [ ] Navigate to optimization
7. [ ] Generate suggestions
8. [ ] Apply one suggestion
9. [ ] Navigate to matching
10. [ ] Run match analysis
11. [ ] Export match results

**Expected**: All steps succeed, no errors

---

#### Test 2: Cost Dashboard
1. [ ] Login as admin
2. [ ] Navigate to /admin/costs
3. [ ] Verify summary cards load
4. [ ] Check cost trend chart renders
5. [ ] Check task breakdown chart renders
6. [ ] Verify recent calls table populates
7. [ ] Export CSV successfully

**Expected**: All data displays, charts interactive

---

#### Test 3: Mobile Experience
1. [ ] Open on mobile device (or DevTools)
2. [ ] Test at 375px width
3. [ ] Upload resume
4. [ ] Navigate through pages
5. [ ] Verify charts work on touch
6. [ ] Verify buttons tappable

**Expected**: All features work, no layout issues

---

#### Test 4: Error Handling
1. [ ] Disconnect internet
2. [ ] Try to upload resume
3. [ ] Verify error message displays
4. [ ] Reconnect internet
5. [ ] Retry, verify works

**Expected**: Graceful error messages, retry works

---

### Monitoring Setup

#### Sentry Error Tracking
**Verify**:
- [ ] Frontend errors sent to Sentry
- [ ] Backend errors sent to Sentry
- [ ] Source maps uploaded
- [ ] Alerts configured

**Test**:
```javascript
// Trigger test error in frontend
throw new Error("Sentry test error");
```

**Expected**: Error appears in Sentry dashboard

---

#### Railway Logs
**Check**:
- [ ] Application logs visible
- [ ] No critical errors
- [ ] Request/response logs
- [ ] Cost tracker logs

---

#### Vercel Analytics
**Enable**:
- [ ] Web Vitals tracking
- [ ] Page view analytics
- [ ] Geographic data

---

## Production URLs

### Frontend
- **Production**: https://your-app.vercel.app
- **Staging**: https://your-app-git-staging.vercel.app
- **Dashboard**: https://vercel.com/your-org/your-app

### Backend
- **API**: https://your-backend.up.railway.app
- **Docs**: https://your-backend.up.railway.app/docs
- **Dashboard**: https://railway.app/project/your-project

### Monitoring
- **Sentry**: https://sentry.io/organizations/your-org
- **Uptime**: (TBD - consider UptimeRobot)

---

## Rollback Plan

### If Frontend Deploy Fails
```bash
# Vercel Dashboard → Deployments → Previous Deploy → Promote to Production
# Or via CLI:
vercel rollback
```

### If Backend Deploy Fails
```bash
# Railway Dashboard → Deployments → Select Previous → Rollback
# Or redeploy previous commit:
git revert HEAD
git push origin main
```

### If Database Issue
```bash
# Restore from Supabase backup
# Navigate: Supabase Dashboard → Database → Backups → Restore
```

---

## Security Checklist

### Frontend
- [ ] No API keys in client-side code
- [ ] All secrets in environment variables
- [ ] HTTPS enforced
- [ ] CSP headers configured
- [ ] No sensitive data in logs

### Backend
- [ ] CORS configured correctly
- [ ] JWT secret secure
- [ ] Service role key not exposed
- [ ] File upload size limited
- [ ] Rate limiting enabled
- [ ] Virus scanning active

### Database
- [ ] RLS policies enabled
- [ ] Row-level security tested
- [ ] No cross-user data leaks
- [ ] Backups automated

---

## Performance Benchmarks

### Expected Metrics
- **Page Load**: < 2s (75th percentile)
- **API Response**: < 500ms (95th percentile)
- **LLM Extraction**: 10-30s (acceptable)
- **File Upload**: < 5s for 2MB PDF

### Monitoring
- [ ] Set up Vercel Analytics
- [ ] Configure Sentry Performance
- [ ] Monitor Railway metrics
- [ ] Set alert thresholds

---

## Cost Estimates (Monthly)

### Vercel (Hobby Plan)
- **Cost**: $0 (free tier)
- **Limits**: 100GB bandwidth, unlimited requests
- **Upgrade**: $20/mo for Pro if needed

### Railway (Developer Plan)
- **Cost**: $5-20/mo (usage-based)
- **Includes**: Web + Redis + 500MB storage
- **Estimate**: ~$10/mo for MVP traffic

### Supabase (Free Plan)
- **Cost**: $0 (free tier)
- **Limits**: 500MB storage, 2GB bandwidth
- **Upgrade**: $25/mo for Pro if needed

### Anthropic (Claude API)
- **Cost**: Pay-as-you-go
- **Estimate**: $20-100/mo depending on usage
- **Model**: Claude 3 Sonnet ($3/$15 per 1M tokens)

### Sentry (Developer Plan)
- **Cost**: $0 (free tier)
- **Limits**: 5K errors/month
- **Upgrade**: $26/mo for Team if needed

**Total Estimated Cost**: $30-130/mo

---

## Next Steps After Deployment

1. [ ] **Domain Setup**
   - Purchase domain
   - Configure DNS
   - Add to Vercel
   - Update CORS in backend

2. [ ] **Custom Domain Email**
   - Set up admin@yourdomain.com
   - Configure support@yourdomain.com

3. [ ] **Documentation**
   - User guide
   - API documentation
   - Admin handbook

4. [ ] **Marketing**
   - Landing page optimization
   - SEO setup
   - Social media

5. [ ] **Analytics**
   - Google Analytics
   - Mixpanel/PostHog
   - User behavior tracking

---

## Completion Criteria

- [ ] Backend deployed to Railway ✅
- [ ] Frontend deployed to Vercel ✅
- [ ] All environment variables configured ✅
- [ ] Database migrations run ✅
- [ ] Sentry monitoring active ✅
- [ ] Smoke tests pass ✅
- [ ] Mobile experience verified ✅
- [ ] Production URLs documented ✅
- [ ] Rollback plan tested ✅
- [ ] Cost tracking confirmed ✅

**When all checked**: 🚀 **MVP IS LIVE** 🚀

---

**Estimated Total Deployment Time**: 2 hours  
**Current Status**: ⏳ Ready to begin  
**Next Action**: Start with Task 5.1 (Vercel signup)
