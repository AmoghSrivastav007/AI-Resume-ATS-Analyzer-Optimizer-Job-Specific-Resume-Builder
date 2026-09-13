from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routers.jobs import router as jobs_router
from routers.resumes import router as resumes_router


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

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resumes_router)
app.include_router(jobs_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
