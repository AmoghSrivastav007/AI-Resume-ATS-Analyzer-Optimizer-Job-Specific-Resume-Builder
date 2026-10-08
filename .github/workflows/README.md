# CI/CD Pipeline Documentation

## Overview

This directory contains GitHub Actions workflows for automated testing, evaluation, and deployment.

## Workflow: `ci-cd.yml`

**Trigger**: Push to `main` or pull request to `main`

### Pipeline Stages

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Actions CI/CD                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │   Stage 1: Backend Tests      │
              │   • Setup Python 3.11         │
              │   • Install dependencies      │
              │   • Run pytest (130 tests)    │
              │   • Generate coverage report  │
              │   Duration: ~20 seconds       │
              └───────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │  Stage 2: Evaluation Tests    │
              │   • Validate 62-file benchmark│
              │   • Run hallucination eval    │
              │   • Check for critical issues │
              │   • FAIL if fraud detected    │
              │   Duration: ~2 minutes        │
              └───────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │   Stage 3: Frontend Tests     │
              │   • Setup Node.js 20.x        │
              │   • Install dependencies      │
              │   • Run ESLint                │
              │   • Build Next.js app         │
              │   Duration: ~30 seconds       │
              └───────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │   Stage 4: Deploy Frontend    │
              │   • Only on main branch       │
              │   • Deploy to Vercel          │
              │   • Automatic rollback on fail│
              │   Duration: ~2 minutes        │
              └───────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │   Stage 5: Deploy Backend     │
              │   • Only on main branch       │
              │   • Deploy to Railway         │
              │   • Web + Worker services     │
              │   Duration: ~3 minutes        │
              └───────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │  Stage 6: Health Checks       │
              │   • Wait for services up      │
              │   • Test /health endpoint     │
              │   • Test /health/ready        │
              │   Duration: ~10 seconds       │
              └───────────────────────────────┘
                              │
                              ▼
                    ┌──────────────┐
                    │  DEPLOYED ✅  │
                    └──────────────┘
```

## Test Suite Breakdown

### Backend Tests (130 tests)
- **Services**: 45 tests
- **Routers**: 38 tests
- **Models**: 25 tests
- **Parser**: 22 tests

**Pass Rate**: 94% (122/130)

### Evaluation Tests
- **Benchmark Files**: 62 files (15 PDFs, 17 JDs, 10 ground truth, 5 adversarial)
- **Validation**: 100% structural validation
- **Hallucination Detection**: 5/5 fraud patterns detected

## Deployment Flow

### On Pull Request
- ✅ Run all tests
- ✅ Post results as PR comment
- ❌ Do NOT deploy

### On Push to Main
- ✅ Run all tests
- ✅ Deploy to Vercel (frontend)
- ✅ Deploy to Railway (backend)
- ✅ Run health checks
- ❌ Rollback if health checks fail

## Required Secrets

Add these secrets in GitHub repository settings (Settings → Secrets and variables → Actions):

### Vercel Deployment
```
VERCEL_TOKEN          # Vercel API token
VERCEL_ORG_ID         # Organization ID
VERCEL_PROJECT_ID     # Project ID
```

### Railway Deployment
```
RAILWAY_TOKEN         # Railway API token
```

### Optional (for test environment)
```
SUPABASE_URL                  # Test database
SUPABASE_ANON_KEY            # Test auth key
SUPABASE_SERVICE_ROLE_KEY    # Test admin key
SUPABASE_JWT_SECRET          # Test JWT secret
ANTHROPIC_API_KEY            # For evaluation tests
REDIS_URL                    # Test Redis
```

## Getting Tokens

### Vercel Token
```bash
# Install Vercel CLI
npm install -g vercel

# Login and get token
vercel login
vercel whoami
vercel --scope your-team

# Get IDs
vercel link
# Saves .vercel/project.json with orgId and projectId
```

### Railway Token
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Generate token
railway token create
```

## Manual Workflow Triggers

```bash
# Trigger workflow manually
gh workflow run ci-cd.yml

# Watch workflow progress
gh run watch

# List recent runs
gh run list --workflow=ci-cd.yml

# View logs for failed run
gh run view <run-id> --log-failed
```

## Monitoring

### GitHub Actions Dashboard
- View at: https://github.com/your-org/resume-analyzer/actions
- Shows all workflow runs
- Download logs and artifacts
- Re-run failed workflows

### Notifications
Configure in: Settings → Notifications → Actions
- Email on workflow failure
- Slack/Discord webhooks (optional)

## Troubleshooting

### Tests Failing Locally But Pass in CI
- Check Python/Node.js versions match
- Verify environment variables
- Run `pytest --verbose` for detailed output

### Deployment Failing
- Check Railway logs: `railway logs --service web`
- Verify all secrets are set correctly
- Test health endpoint manually: `curl https://your-api.railway.app/health`

### Health Checks Failing
- Check Supabase connection
- Check Redis connection
- Verify environment variables on Railway
- View Railway service logs

### High Build Times
- Current times:
  - Backend tests: ~20s
  - Evaluation: ~2m
  - Frontend: ~30s
  - Deploy: ~5m
  - **Total**: ~8 minutes

- To optimize:
  - Cache Python dependencies
  - Cache Node modules
  - Run tests in parallel
  - Skip evaluation on non-main branches

## Best Practices

1. **Always run tests locally before pushing**
   ```bash
   cd apps/api && pytest
   cd apps/web && npm run lint && npm run build
   ```

2. **Use feature branches**
   - Create branch: `git checkout -b feature/your-feature`
   - Push and create PR
   - CI runs automatically
   - Merge after approval + passing tests

3. **Monitor deployment**
   - Check GitHub Actions after merge
   - Verify health endpoints
   - Check Sentry for errors
   - Review cost dashboard

4. **Rollback if needed**
   - Vercel: `vercel rollback <deployment-url>`
   - Railway: `railway rollback`
   - Git: `git revert HEAD && git push`

## Related Documentation

- **Main Deployment Guide**: `../../DEPLOYMENT.md`
- **Backend Config**: `../../apps/api/.env.example`
- **Frontend Config**: `../../apps/web/.env.example`
- **Cost Tracking**: `../../apps/api/services/cost_tracker.py`

---

**Last Updated**: 2024-03-15  
**Workflow Version**: 1.0.0
