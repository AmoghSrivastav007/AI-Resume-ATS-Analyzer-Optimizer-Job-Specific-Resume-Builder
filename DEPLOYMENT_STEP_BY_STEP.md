# Step-by-Step Production Deployment Guide

**Target**: Deploy Resume ATS Analyzer MVP to production  
**Platforms**: Vercel (Frontend) + Railway (Backend)  
**Estimated Time**: 2 hours  
**Date**: October 8, 2026

---

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] GitHub account with repository access
- [ ] Credit card (for Anthropic API - pay-as-you-go)
- [ ] Email access (for verification codes)
- [ ] Browser with good internet connection
- [ ] Supabase project already set up (from development)
- [ ] All environment variable values ready (see DEPLOYMENT_ENVIRONMENT_VARIABLES.md)

---

## Phase 1: Account Setup (30 minutes)

### Step 1.1: Vercel Account Setup (10 min)

#### A. Sign Up
1. Go to https://vercel.com/signup
2. Click **"Continue with GitHub"**
3. Authorize Vercel to access your GitHub account
4. Select **Hobby (Free)** plan
5. Verify your email if prompted

#### B. Import Repository
1. Click **"Add New..." → "Project"**
2. Search for **"Resume analyser"** repository
3. Click **"Import"**
4. Configure project:
   - **Framework Preset**: Next.js (auto-detected)
   - **Root Directory**: `apps/web`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
   - **Install Command**: `npm install --legacy-peer-deps`
5. Click **"Deploy"** (it will fail - expected!)

**Expected Result**: 
- ❌ Build fails with "Missing environment variables"
- ✅ Project dashboard created
- ✅ URL assigned: `https://your-project-name.vercel.app`

**Save this**:
```
Vercel Project URL: https://_________________________.vercel.app
Vercel Project ID: _________________________
```

---

### Step 1.2: Railway Account Setup (10 min)

#### A. Sign Up
1. Go to https://railway.app/login
2. Click **"Login with GitHub"**
3. Authorize Railway to access your GitHub account
4. Verify your email if prompted

#### B. Create New Project
1. Click **"+ New Project"**
2. Select **"Deploy from GitHub repo"**
3. Search for **"Resume analyser"** repository
4. Click on your repository
5. Railway auto-detects configuration:
   - ✅ Finds `Procfile`
   - ✅ Detects Python app
   - ✅ Creates "web" service

**Expected Result**:
- ✅ Project created
- ✅ Web service added
- ⏳ First deploy starts automatically (will fail without env vars)

**Save this**:
```
Railway Project URL: https://railway.app/project/_____________________
Railway Service URL: https://_________________________.up.railway.app
```

#### C. Add Redis Service
1. In your Railway project, click **"+ New"**
2. Select **"Database"**
3. Click **"Add Redis"**
4. Redis service starts automatically
5. Verify `REDIS_URL` appears in web service variables

**Expected Result**:
- ✅ Redis service running
- ✅ REDIS_URL auto-added to web service

---

### Step 1.3: Sentry Account Setup (10 min)

#### A. Sign Up
1. Go to https://sentry.io/signup
2. Click **"Continue with GitHub"** (or email)
3. Create organization name: **"Resume Analyzer"** (or your choice)
4. Select **Developer (Free)** plan

#### B. Create Frontend Project
1. Click **"Create Project"**
2. Select platform: **"Next.js"**
3. Project name: **"frontend"** or **"resume-analyzer-frontend"**
4. Alert frequency: **"On every new issue"**
5. Click **"Create Project"**
6. **Copy the DSN** (looks like: `https://abc@xyz.ingest.sentry.io/123`)

**Save this**:
```
Frontend Sentry DSN: https://________________________________
```

#### C. Create Backend Project
1. Click organization name → **"Create Project"**
2. Select platform: **"Python"** or **"FastAPI"**
3. Project name: **"backend"** or **"resume-analyzer-backend"**
4. Alert frequency: **"On every new issue"**
5. Click **"Create Project"**
6. **Copy the DSN**

**Save this**:
```
Backend Sentry DSN: https://________________________________
```

---

## Phase 2: Configure Environment Variables (15 minutes)

### Step 2.1: Vercel Environment Variables (5 min)

1. Go to Vercel Dashboard → Your Project
2. Click **"Settings"** tab
3. Click **"Environment Variables"** in left sidebar
4. Add each variable below:

#### Variable 1: NEXT_PUBLIC_API_URL
```
Key: NEXT_PUBLIC_API_URL
Value: [Your Railway URL from Step 1.2]
Example: https://resume-analyzer-backend.up.railway.app
```
Select: ✅ Production ✅ Preview ✅ Development

#### Variable 2: NEXT_PUBLIC_SUPABASE_URL
```
Key: NEXT_PUBLIC_SUPABASE_URL
Value: [From Supabase Dashboard → Settings → API → URL]
Example: https://abcdefghijklmn.supabase.co
```
Select: ✅ Production ✅ Preview ✅ Development

#### Variable 3: NEXT_PUBLIC_SUPABASE_ANON_KEY
```
Key: NEXT_PUBLIC_SUPABASE_ANON_KEY
Value: [From Supabase Dashboard → Settings → API → anon public key]
Example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
Select: ✅ Production ✅ Preview ✅ Development

#### Variable 4: NEXT_PUBLIC_SENTRY_DSN
```
Key: NEXT_PUBLIC_SENTRY_DSN
Value: [Frontend DSN from Step 1.3]
Example: https://abc123@o123.ingest.sentry.io/456
```
Select: ✅ Production ✅ Preview ✅ Development

**Verification**:
- [ ] All 4 variables added
- [ ] All have 3 environments selected
- [ ] No typos in URLs

---

### Step 2.2: Railway Environment Variables (10 min)

1. Go to Railway Dashboard → Your Project
2. Click on **"web"** service
3. Click **"Variables"** tab
4. Add each variable below:

#### Variable 1: SUPABASE_URL
```
SUPABASE_URL
[Same as frontend NEXT_PUBLIC_SUPABASE_URL]
```

#### Variable 2: SUPABASE_KEY
```
SUPABASE_KEY
[From Supabase Dashboard → Settings → API → service_role key]
⚠️ NOT the anon key! This is different!
```

#### Variable 3: SUPABASE_JWT_SECRET
```
SUPABASE_JWT_SECRET
[From Supabase Dashboard → Settings → API → JWT Secret]
```

#### Variable 4: ANTHROPIC_API_KEY
```
ANTHROPIC_API_KEY
[From https://console.anthropic.com/settings/keys]
⚠️ Must have payment method added to Anthropic account!
```

#### Variable 5: COST_TRACKING_ENABLED
```
COST_TRACKING_ENABLED
true
```

#### Variable 6: ALLOWED_ORIGINS
```
ALLOWED_ORIGINS
[Your Vercel URL from Step 1.1, include wildcards for preview deployments]
Example: https://your-app.vercel.app,https://your-app-*.vercel.app
```

#### Variable 7: MAX_FILE_SIZE_MB
```
MAX_FILE_SIZE_MB
10
```

#### Variable 8: SENTRY_DSN
```
SENTRY_DSN
[Backend DSN from Step 1.3]
```

#### Variable 9: REDIS_URL (Verify)
```
REDIS_URL
[Should be auto-populated from Step 1.2C]
If not: redis://default:[password]@redis.railway.internal:6379
```

**Verification**:
- [ ] All 9 variables added
- [ ] REDIS_URL is present (auto-added)
- [ ] SUPABASE_KEY is service_role (not anon)
- [ ] ANTHROPIC_API_KEY has billing enabled

---

## Phase 3: Database Setup (10 minutes)

### Step 3.1: Supabase Extensions

1. Go to Supabase Dashboard
2. Navigate to **Database → Extensions**
3. Enable these extensions (if not already):
   - ✅ `vector` (Search for "pgvector")
   - ✅ `pg_trgm`
   - ✅ `uuid-ossp`

---

### Step 3.2: Run Migrations

**Option A: Via Supabase SQL Editor (Recommended)**

1. Go to Supabase Dashboard → **SQL Editor**
2. Click **"+ New query"**
3. For each migration file in order:

```bash
# Run these in order (in apps/api/migrations/):
1. 001_extensions_and_functions.sql
2. 002_tables.sql
3. 003_hnsw_indexes.sql
4. 004_rls_policies.sql
5. 005_storage.sql
6. 006_parse_fields.sql
7. 007_score_breakdown.sql
8. 008_job_postings.sql
9. 009_step6_matching.sql
10. 010_export_jobs.sql
```

For each file:
- Open `apps/api/migrations/00X_name.sql`
- Copy entire contents
- Paste into Supabase SQL Editor
- Click **"Run"**
- Verify success message
- Move to next file

**Option B: Via psql (Advanced)**

```bash
# Get connection string from Supabase → Settings → Database
psql "postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres"

# Run migrations
\i apps/api/migrations/001_extensions_and_functions.sql
\i apps/api/migrations/002_tables.sql
# ... etc
```

**Verification**:
- [ ] All 10 migrations run successfully
- [ ] Tables visible in Supabase → Database → Tables
- [ ] RLS policies active (check Table Editor shows lock icons)

---

### Step 3.3: Configure Storage Bucket

1. Go to Supabase Dashboard → **Storage**
2. Click **"Create a new bucket"**
3. Configure:
   - **Name**: `resumes`
   - **Public bucket**: ❌ OFF (private)
   - **Allowed MIME types**: 
     - `application/pdf`
     - `application/msword`
     - `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
   - **File size limit**: `10485760` (10 MB in bytes)
4. Click **"Create bucket"**

**Verification**:
- [ ] "resumes" bucket exists
- [ ] Bucket is private
- [ ] File size limit is 10 MB

---

## Phase 4: Deploy Backend (20 minutes)

### Step 4.1: Trigger Railway Deploy

Railway should already be deploying. If not:

1. Go to Railway Dashboard → Your Project → web service
2. Click **"Deployments"** tab
3. Click **"Deploy"** button (if not already deploying)

**Monitor the build**:
- [ ] Build logs show: "Installing dependencies..."
- [ ] Build logs show: "Starting application..."
- [ ] Deploy status: ✅ Success

**Expected Build Time**: 3-5 minutes

---

### Step 4.2: Verify Backend is Running

#### A. Check Health Endpoint
```bash
# Replace with your Railway URL
curl https://your-backend.up.railway.app/health

# Expected response:
{"status":"healthy","version":"1.0.0"}
```

#### B. Check API Docs
Open in browser:
```
https://your-backend.up.railway.app/docs
```

**Should see**: Swagger UI with all API endpoints

#### C. Check Environment
```bash
# Should return 200 OK (will say unauthorized if working)
curl https://your-backend.up.railway.app/api/resumes

# Should return {"detail":"Missing or invalid Authorization header..."}
```

**Verification**:
- [ ] /health returns 200
- [ ] /docs loads Swagger UI
- [ ] /api/resumes returns 401 (correct - needs auth)
- [ ] No 500 errors in Railway logs

---

### Step 4.3: Test Database Connection

1. Go to Railway → web service → **"Logs"** tab
2. Look for startup logs
3. Verify no database errors
4. Should see: "Application startup complete"

**If you see errors**:
- Check SUPABASE_URL is correct
- Check SUPABASE_KEY is service_role key
- Check Supabase project is not paused

---

## Phase 5: Deploy Frontend (20 minutes)

### Step 5.1: Update CORS Configuration

**Important**: Update backend ALLOWED_ORIGINS now that you know the Vercel URL

1. Go to Railway → web service → Variables
2. Find `ALLOWED_ORIGINS`
3. Update value to include your actual Vercel URL:
```
https://your-actual-app.vercel.app,https://your-actual-app-*.vercel.app,https://*.vercel.app
```
4. Click **"Redeploy"** to apply changes

---

### Step 5.2: Trigger Vercel Redeploy

Since we added environment variables after first deploy:

1. Go to Vercel Dashboard → Your Project
2. Click **"Deployments"** tab
3. Find the failed deployment
4. Click **"⋯"** (three dots) → **"Redeploy"**
5. Or: Click **"Redeploy"** button at top

**Monitor the build**:
- [ ] Build logs show: "Installing dependencies..."
- [ ] Build logs show: "Compiled successfully"
- [ ] Build logs show: "Exporting..."
- [ ] Deploy status: ✅ Ready

**Expected Build Time**: 2-4 minutes

---

### Step 5.3: Verify Frontend is Running

#### A. Visit Homepage
```
https://your-app.vercel.app
```

**Should see**: Landing page or login screen

#### B. Check API Connection
1. Open browser DevTools (F12)
2. Go to **Network** tab
3. Visit a page that makes API calls
4. Check requests go to Railway backend URL
5. Verify no CORS errors

#### C. Test Login Flow
1. Click **"Sign Up"** or **"Login"**
2. Enter test credentials
3. Should redirect to dashboard
4. No console errors

**Verification**:
- [ ] Homepage loads
- [ ] No CORS errors in console
- [ ] Can login/signup
- [ ] Dashboard loads after login

---

## Phase 6: End-to-End Testing (10 minutes)

### Test 1: Resume Upload Flow

1. **Login** to your deployed app
2. **Upload** a test resume (PDF)
3. **Wait** for parsing (10-30 seconds)
4. **Verify** analysis page loads with:
   - Quality score
   - Parsed content
   - Quality issues

**Expected**: ✅ Resume parsed and analyzed

---

### Test 2: Optimization Page

1. Navigate to **Optimize** tab
2. Click **"Generate Suggestions"**
3. Wait for AI to generate (10-20 seconds)
4. **Verify** suggestions appear
5. Click **"Apply"** on one suggestion
6. **Verify** it's marked as applied

**Expected**: ✅ Suggestions generated and can be applied

---

### Test 3: Cost Dashboard

1. Navigate to `/admin/costs`
2. **Verify**:
   - Summary cards show data
   - Cost trend chart renders
   - Task breakdown chart renders
   - Recent calls table has entries

**Expected**: ✅ Cost data tracked from previous API calls

---

### Test 4: Mobile Experience

1. Open DevTools (F12)
2. Toggle **device toolbar** (Ctrl+Shift+M)
3. Select **iPhone 12 Pro** or **375px** width
4. Navigate through app:
   - Upload resume
   - View analysis
   - Check optimization page
   - Check cost dashboard (if admin)

**Expected**: ✅ All pages work on mobile, no layout issues

---

### Test 5: Error Handling

1. Open DevTools → **Network** tab
2. Set throttling to **"Offline"**
3. Try to upload a resume
4. **Verify** error message appears
5. Set back to **"No throttling"**
6. Click retry
7. **Verify** upload works

**Expected**: ✅ Graceful error messages, retry works

---

## Phase 7: Post-Deployment Configuration (10 minutes)

### Step 7.1: Configure Sentry Alerts

#### Frontend Project
1. Go to Sentry → Frontend Project → **Settings → Alerts**
2. Click **"Create Alert Rule"**
3. Configure:
   - **When**: Error rate > 10 errors per hour
   - **Then**: Send notification to email
4. Click **"Create Rule"**

#### Backend Project
1. Same steps for backend project
2. Additional rule:
   - **When**: New issue created
   - **Then**: Send notification

---

### Step 7.2: Test Sentry Integration

#### Frontend Test
1. Add this to any frontend page temporarily:
```typescript
throw new Error("Sentry frontend test error");
```
2. Visit that page
3. Check Sentry dashboard for error
4. Remove test code

#### Backend Test
```bash
# Make a request that will error
curl https://your-backend.up.railway.app/api/resumes/invalid-id

# Check Sentry backend project for error
```

**Verification**:
- [ ] Frontend errors appear in Sentry
- [ ] Backend errors appear in Sentry
- [ ] Alerts configured

---

### Step 7.3: Set Up Custom Domain (Optional)

If you have a domain:

#### Vercel Domain
1. Go to Vercel → Project → **Settings → Domains**
2. Click **"Add"**
3. Enter your domain: `app.yourdomain.com`
4. Follow DNS configuration instructions
5. Wait for DNS propagation (5-60 min)

#### Railway Domain
1. Go to Railway → web service → **Settings**
2. Under **"Networking"**, click **"Generate Domain"**
3. Or add custom domain

**Then update**:
- [ ] NEXT_PUBLIC_API_URL in Vercel (if Railway domain changed)
- [ ] ALLOWED_ORIGINS in Railway (include new frontend domain)

---

## Phase 8: Monitoring and Maintenance

### Step 8.1: Bookmark These URLs

```
Production URLs:
✅ Frontend: https://your-app.vercel.app
✅ Backend: https://your-backend.up.railway.app
✅ API Docs: https://your-backend.up.railway.app/docs

Dashboards:
✅ Vercel: https://vercel.com/dashboard
✅ Railway: https://railway.app/dashboard
✅ Supabase: https://app.supabase.com
✅ Sentry: https://sentry.io/organizations/your-org
✅ Anthropic: https://console.anthropic.com
```

---

### Step 8.2: Set Up Monitoring

#### Uptime Monitoring (Optional)
Consider using:
- **UptimeRobot** (free, 50 monitors)
- **Pingdom** (free tier available)
- **Better Uptime** (modern, free tier)

Monitor:
- Frontend: https://your-app.vercel.app
- Backend: https://your-backend.up.railway.app/health

---

### Step 8.3: Create Backup Plan

#### Database Backups
Supabase automatically backs up daily (Pro plan) or weekly (Free plan)

To manually backup:
1. Supabase → Database → **Backups**
2. Click **"Create backup"**
3. Store backup metadata

#### Environment Variables Backup
Save all environment variables to secure location:
1. Use password manager
2. Or encrypted file in safe location
3. Never commit to git!

---

## Troubleshooting Guide

### Issue: Vercel build fails

**Check**:
1. Build logs for specific error
2. Environment variables set correctly
3. `apps/web` is set as root directory
4. Node version compatibility (16+)

**Solution**:
```bash
# In Vercel project settings:
Root Directory: apps/web
Build Command: npm run build
Install Command: npm install --legacy-peer-deps
Output Directory: .next
Node Version: 18.x (auto-detect)
```

---

### Issue: Railway build fails

**Check**:
1. Deployment logs for error
2. Python version (3.11 recommended)
3. All environment variables set
4. `Procfile` in root directory

**Solution**:
1. Verify `Procfile` exists:
```
web: cd apps/api && uvicorn main:app --host 0.0.0.0 --port $PORT
```
2. Check `requirements.txt` has no syntax errors
3. Ensure `$PORT` is used (Railway assigns this)

---

### Issue: CORS errors

**Symptoms**: "CORS policy" errors in browser console

**Solution**:
1. Check ALLOWED_ORIGINS in Railway includes exact Vercel URL
2. Include preview domains: `https://your-app-*.vercel.app`
3. Redeploy Railway after changing
4. Clear browser cache

---

### Issue: "Invalid JWT" errors

**Symptoms**: 401 errors when making authenticated requests

**Solution**:
1. Verify SUPABASE_JWT_SECRET matches Supabase exactly
2. Check no extra spaces or newlines
3. Verify SUPABASE_KEY is service_role key
4. Try logging out and back in

---

### Issue: File uploads fail

**Symptoms**: Error when uploading resume

**Solution**:
1. Check Supabase storage bucket "resumes" exists
2. Verify bucket is created in correct project
3. Check file size < 10 MB
4. Check MIME type is allowed
5. Verify SUPABASE_KEY has storage permissions

---

### Issue: LLM calls fail

**Symptoms**: "Anthropic API error" in logs

**Solution**:
1. Verify ANTHROPIC_API_KEY is correct
2. Check Anthropic account has payment method
3. Check account has API credits
4. Verify key has correct permissions
5. Check API rate limits not exceeded

---

### Issue: Cost tracking shows no data

**Symptoms**: Cost dashboard is empty

**Solution**:
1. Check REDIS_URL is set in Railway
2. Verify Redis service is running
3. Check COST_TRACKING_ENABLED=true
4. Make test API call (upload resume)
5. Check Railway logs for Redis connection errors

---

## Success Criteria Checklist

### Deployment Complete When:

#### Backend (Railway)
- [ ] Build succeeds
- [ ] /health endpoint returns 200
- [ ] /docs loads Swagger UI
- [ ] Database connected (no errors in logs)
- [ ] Redis connected
- [ ] Environment variables verified
- [ ] Sentry receiving events

#### Frontend (Vercel)
- [ ] Build succeeds
- [ ] Homepage loads
- [ ] Can login/signup
- [ ] Dashboard loads
- [ ] No CORS errors
- [ ] API calls reach backend
- [ ] Sentry receiving events

#### End-to-End
- [ ] Can upload resume
- [ ] Resume gets parsed
- [ ] Analysis shows results
- [ ] Can generate optimizations
- [ ] Can view matches (if JD uploaded)
- [ ] Cost dashboard shows data
- [ ] Mobile experience works
- [ ] Error handling graceful

---

## Post-Deployment Tasks

### Immediate (Within 24 hours)
- [ ] Test all major user flows
- [ ] Monitor error rates in Sentry
- [ ] Check cost dashboard for unexpected spikes
- [ ] Verify email notifications working
- [ ] Test on real mobile device

### Short Term (Within 1 week)
- [ ] Set up custom domain
- [ ] Configure email templates (Supabase)
- [ ] Add analytics (Google Analytics/PostHog)
- [ ] Create user documentation
- [ ] Set up automated backups
- [ ] Configure monitoring alerts

### Ongoing
- [ ] Monitor Anthropic API costs daily
- [ ] Review Sentry errors weekly
- [ ] Check Railway usage monthly
- [ ] Update dependencies monthly
- [ ] Review security logs monthly

---

## Cost Monitoring

### Expected Monthly Costs

**Vercel** (Hobby): $0  
**Railway**: $5-20 (usage-based)  
**Supabase** (Free): $0  
**Anthropic**: $20-100 (usage-based)  
**Sentry** (Developer): $0  

**Total**: $25-120/month

### Cost Alerts to Set

1. **Anthropic**: Set up billing alert at $50, $100
2. **Railway**: Monitor usage in dashboard
3. **Vercel**: Will notify if approaching limits

---

## Rollback Procedures

### If Frontend Deploy Breaks
```bash
# In Vercel dashboard:
Deployments → Find last working deploy → Promote to Production
```

### If Backend Deploy Breaks
```bash
# In Railway dashboard:
Deployments → Find last working deploy → Rollback
```

### If Database Issue
```bash
# In Supabase:
Database → Backups → Select backup → Restore
```

---

## 🎉 Deployment Complete!

When all checks pass:

✅ **MVP IS LIVE**

Share your production URL:
```
🚀 https://your-app.vercel.app
```

---

**Next Steps**:
1. Share with beta users
2. Gather feedback
3. Monitor metrics
4. Iterate and improve

**Congratulations on shipping your MVP!** 🎊

---

**Document Version**: 1.0  
**Last Updated**: October 8, 2026  
**Deployment Status**: Ready to begin
