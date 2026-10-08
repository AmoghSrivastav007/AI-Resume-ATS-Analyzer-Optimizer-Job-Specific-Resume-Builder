from contextlib import asynccontextmanager
import time
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from config import get_settings
from middleware.rate_limit import limiter, rate_limit_exceeded_handler
from routers.analyses import router as analyses_router
from routers.blocks import router as blocks_router
from routers.costs import router as costs_router
from routers.exports import router as exports_router
from routers.job_postings import router as job_postings_router
from routers.jobs import router as jobs_router
from routers.matching import router as matching_router
from routers.optimize import router as optimize_router
from routers.resumes import router as resumes_router
from routers.versions import router as versions_router

# Initialize Sentry
settings = get_settings()
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        profiles_sample_rate=settings.sentry_profiles_sample_rate,
        integrations=[
            FastApiIntegration(),
            RedisIntegration(),
        ],
        # Send PII (personally identifiable information)
        send_default_pii=False,
        # Release tracking
        release=settings.sentry_release,
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    required = [
        settings.supabase_url,
        settings.supabase_anon_key,
        settings.supabase_service_role_key,
        settings.supabase_jwt_secret,
    ]
    missing = [name for name, value in zip(
        ["SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_JWT_SECRET"],
        required,
    ) if not value]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        )
    yield


app = FastAPI(title="Resume ATS Analyzer API", lifespan=lifespan)

# Track startup time for health check
app.state.startup_time = datetime.utcnow()

# Add rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware for performance monitoring
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

app.include_router(resumes_router)
app.include_router(jobs_router)
app.include_router(analyses_router)
app.include_router(job_postings_router)
app.include_router(matching_router)
app.include_router(optimize_router)
app.include_router(blocks_router)
app.include_router(versions_router)
app.include_router(exports_router)
app.include_router(costs_router)


@app.get("/health")
async def health() -> dict[str, str | float]:
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        - status: "ok" if service is healthy
        - uptime_seconds: seconds since startup
        - timestamp: current UTC timestamp
    """
    uptime = (datetime.utcnow() - app.state.startup_time).total_seconds()
    return {
        "status": "ok",
        "uptime_seconds": uptime,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.get("/health/ready")
async def readiness() -> dict[str, str | bool]:
    """
    Readiness check for Kubernetes/orchestration platforms.
    
    Returns:
        - ready: true if service can accept traffic
        - checks: dict of individual service checks
    """
    from supabase import create_client
    
    checks = {}
    
    # Check Supabase connection
    try:
        supabase = create_client(settings.supabase_url, settings.supabase_anon_key)
        # Simple query to verify connection
        supabase.table("resumes").select("id").limit(1).execute()
        checks["supabase"] = True
    except Exception as e:
        checks["supabase"] = False
        sentry_sdk.capture_exception(e)
    
    # Check Redis connection
    try:
        from redis import Redis
        redis_client = Redis.from_url(settings.redis_url)
        redis_client.ping()
        checks["redis"] = True
    except Exception as e:
        checks["redis"] = False
        sentry_sdk.capture_exception(e)
    
    # Overall readiness
    ready = all(checks.values())
    
    return {
        "ready": ready,
        "checks": checks,
    }
