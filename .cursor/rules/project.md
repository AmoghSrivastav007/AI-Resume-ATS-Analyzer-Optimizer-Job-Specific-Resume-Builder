# Resume ATS Analyzer & Optimizer — Project Rules

You are working on "Resume ATS Analyzer & Optimizer" — a resume analysis and JD-matching tool.

FULL SPEC: docs/architecture.md — read the relevant section before implementing anything, every time. Do not guess at requirements that are already specified there.

## SCOPE DISCIPLINE

- Build only what the current step's prompt asks for. Do not add features, pages, tables, or endpoints beyond what is explicitly requested, even if they seem like natural additions.
- Do not simplify or skip requirements that ARE explicitly requested to "save time." If a request is expensive to implement correctly, say so and ask before cutting scope — do not silently produce a weaker version.
- Never fabricate data, mock a working feature with hardcoded fake output, or silently stub out a hard part. If something can't be completed, say so explicitly in your response rather than pretending it works.
- Build exactly the MVP scope from docs/architecture.md §20. Nothing from §16's "Should/Nice/Future" tiers gets built unless a step explicitly calls for it.
- Every step ends with working, runnable code — not a stub, not a TODO-riddled skeleton pretending to be done.
- No invented libraries, no invented API keys, no placeholder logic pretending to be real. If a step needs a real API key you haven't provided yet, it should read from .env and fail loudly and clearly if missing, not silently fake data.

## STACK (do not deviate without being asked)

- Frontend: Next.js (App Router) + TypeScript + Tailwind CSS
- Backend: FastAPI (Python 3.11+)
- Database: PostgreSQL + pgvector, via Supabase (includes auth, storage, row-level security)
- AI: Anthropic API — Claude Haiku-class model for extraction/classification/verification tasks, Claude Sonnet-class model for generation/rewriting tasks. Model names are configured via env vars, never hardcoded.
- Queue: Redis + a lightweight worker (RQ)
- PDF/DOCX parsing: PyMuPDF (fitz) + pymupdf4llm for PDF, python-docx + mammoth for DOCX
- PDF/DOCX generation: python-docx for DOCX, WeasyPrint for PDF
- Testing: pytest (backend), Vitest/Playwright (frontend)

## CODE CONVENTIONS

- Backend: Pydantic models for every request/response and every LLM structured-output schema. Every LLM call must use structured output / JSON mode — never parse free text from a model response.
- All secrets (API keys, DB URLs) via environment variables loaded through a single config module — never inline, never committed.
- Every database write that touches PII goes through the audit_log pattern described in docs/architecture.md §12.
- Match the database schema in docs/architecture.md §9 exactly unless a step says otherwise.
- Match the API routes and response shape convention in docs/architecture.md §10 exactly unless a step says otherwise.

## WHEN UNSURE

Stop and ask a clarifying question rather than guessing and producing something outside spec.
