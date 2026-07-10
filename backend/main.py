"""
PRism AI — FastAPI application entry point.

Routes:
  GET  /health                        → liveness check
  POST /api/analyze                   → full PR analysis (primary endpoint)
  POST /api/analyze/url               → same, URL in body as plain string
  GET  /api/analysis/{analysis_id}    → retrieve cached result (in-memory)
  POST /api/repos/reindex             → force re-index a repository
  GET  /api/config                    → show active provider config (no secrets)

Run:
  cd PRism
  uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import sys
import time
import uuid
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, HttpUrl

# ── Bootstrap: add repo root to sys.path so absolute imports resolve ──────────
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.config import get_settings
from backend.services.analysis_service import AnalysisResult, AnalysisService
from backend.services.github_service import parse_pr_url

logger = logging.getLogger("prism.main")

# ── In-process result cache {analysis_id: AnalysisResult} ────────────────────
# Replace with Redis for multi-worker deployments.
_result_cache: dict[str, AnalysisResult] = {}


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown logic."""
    settings = get_settings()
    logger.info(
        "PRism AI starting — provider=%s  env=%s",
        settings.default_llm_provider.value,
        settings.environment,
    )
    settings.validate_provider_key()
    yield
    logger.info("PRism AI shutting down.")


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="PRism AI",
        description=(
            "Autonomous multi-agent Pull Request review platform. "
            "Analyses GitHub PRs for security, quality, architecture, "
            "documentation, testing, and dependency issues."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,   # must be False when allow_origins=["*"]
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request timing middleware ─────────────────────────────────────────────
    @app.middleware("http")
    async def add_timing_header(request: Request, call_next):
        t0       = time.perf_counter()
        response = await call_next(request)
        elapsed  = round((time.perf_counter() - t0) * 1000, 1)
        response.headers["X-Process-Time-Ms"] = str(elapsed)
        return response

    # ── Global exception handler ──────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception on %s: %s", request.url, exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error":   "internal_server_error",
                "message": "An unexpected error occurred. Please try again.",
                "detail":  str(exc) if get_settings().debug else None,
            },
        )

    return app


app = create_app()


# ── Request / response models ─────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    pr_url:       str   = Field(..., description="Full GitHub PR URL.")
    enable_rag:   bool  = Field(default=True,  description="Include RAG context.")
    skip_indexing: bool = Field(default=False, description="Skip RAG re-indexing.")


class AnalyzeUrlRequest(BaseModel):
    url: str = Field(..., description="GitHub PR URL as plain string.")


class ReindexRequest(BaseModel):
    owner:  str = Field(...)
    repo:   str = Field(...)
    branch: str = Field(default="main")


class HealthResponse(BaseModel):
    status:      str
    version:     str
    provider:    str
    environment: str


class ConfigResponse(BaseModel):
    llm_provider:       str
    embedding_provider: str
    vector_db:          str
    llm_model:          str
    environment:        str
    debug:              bool


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Liveness check",
)
async def health() -> HealthResponse:
    """Returns 200 while the server is running."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        version="1.0.0",
        provider=settings.default_llm_provider.value,
        environment=settings.environment,
    )


@app.get(
    "/api/config",
    response_model=ConfigResponse,
    tags=["System"],
    summary="Active configuration (no secrets)",
)
async def config() -> ConfigResponse:
    """Returns the active provider configuration. Never exposes API keys."""
    from ai.llm.llm_factory import LLMFactory
    settings = get_settings()
    return ConfigResponse(
        llm_provider=settings.default_llm_provider.value,
        embedding_provider=settings.default_embedding_provider.value,
        vector_db=settings.default_vector_db.value,
        llm_model=LLMFactory.get_model_name(),
        environment=settings.environment,
        debug=settings.debug,
    )


@app.post(
    "/api/analyze",
    response_model=AnalysisResult,
    status_code=status.HTTP_200_OK,
    tags=["Analysis"],
    summary="Run full multi-agent PR analysis",
)
async def analyze_pr(request: AnalyzeRequest) -> AnalysisResult:
    """
    Trigger a complete PRism analysis on the given GitHub PR URL.

    - Fetches PR metadata, diffs, and CI check-runs from GitHub
    - Optionally indexes the repository for RAG context
    - Runs 7 specialist agents in parallel
    - Synthesises a BLOCKED / CAUTION / READY_TO_MERGE verdict
    - Returns structured findings and a markdown report

    Typical latency: 15–45 seconds depending on PR size and LLM provider.
    """
    # Validate URL before spinning up the service
    try:
        owner, repo, pr_number = parse_pr_url(request.pr_url)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    service = AnalysisService()
    try:
        result = await service.analyse(
            pr_url=request.pr_url,
            enable_rag=request.enable_rag,
            skip_rag_indexing=request.skip_indexing,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )

    # Cache for /api/analysis/{id} retrieval
    _result_cache[result.analysis_id] = result
    return result


@app.post(
    "/api/analyze/url",
    response_model=AnalysisResult,
    status_code=status.HTTP_200_OK,
    tags=["Analysis"],
    summary="Analyse PR by plain URL (demo-friendly)",
)
async def analyze_pr_by_url(request: AnalyzeUrlRequest) -> AnalysisResult:
    """
    Convenience endpoint for the frontend quick-fill demo chips.
    Accepts a plain URL string and runs analysis with default settings.
    """
    return await analyze_pr(
        AnalyzeRequest(pr_url=request.url, enable_rag=True, skip_indexing=False)
    )


@app.get(
    "/api/analysis/{analysis_id}",
    response_model=AnalysisResult,
    tags=["Analysis"],
    summary="Retrieve a cached analysis result",
)
async def get_analysis(analysis_id: str) -> AnalysisResult:
    """
    Retrieve a previously computed analysis by its ID.
    Results are cached in memory for the lifetime of the process.
    """
    result = _result_cache.get(analysis_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis '{analysis_id}' not found. "
                   "Results are cleared on server restart.",
        )
    return result


@app.get(
    "/api/analysis",
    tags=["Analysis"],
    summary="List recent analyses",
)
async def list_analyses(limit: int = 20) -> list[dict]:
    """Return a list of recent cached analyses (ID + verdict + PR title)."""
    recent = list(reversed(list(_result_cache.values())))[:limit]
    return [
        {
            "analysis_id":  r.analysis_id,
            "pr_title":     r.pr_title,
            "pr_url":       r.pr_url,
            "verdict":      r.verdict,
            "confidence":   r.confidence_score,
            "analysed_at":  r.analysed_at,
            "latency_s":    r.latency_seconds,
        }
        for r in recent
    ]


@app.post(
    "/api/repos/reindex",
    tags=["RAG"],
    summary="Force re-index a repository for RAG",
    status_code=status.HTTP_202_ACCEPTED,
)
async def reindex_repository(request: ReindexRequest) -> dict:
    """
    Drop and rebuild the vector store index for the given repository.
    Use this when the codebase has changed significantly since the last index.
    """
    from backend.services.rag_service import RAGService
    service = RAGService()
    try:
        success = await service.reindex(
            owner=request.owner,
            repo=request.repo,
            branch=request.branch,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Reindex failed: {exc}",
        )
    return {
        "status":  "indexed" if success else "skipped",
        "owner":   request.owner,
        "repo":    request.repo,
        "branch":  request.branch,
        "message": (
            "Repository successfully re-indexed."
            if success
            else "Nothing to index — repository may be empty or fetch failed."
        ),
    }


@app.post(
    "/github/webhook",
    tags=["GitHub"],
    summary="Receive GitHub PR webhook events",
    status_code=status.HTTP_202_ACCEPTED,
)
async def github_webhook(request: Request) -> dict:
    """
    Handle incoming GitHub webhook events (push / pull_request).

    Validates the webhook signature and triggers an analysis
    when a PR is opened or synchronised.

    Configure in GitHub: Settings → Webhooks → Content type: application/json
    """
    settings = get_settings()
    secret   = settings.github_webhook_secret

    # ── Signature validation ──────────────────────────────────────────────────
    if secret:
        import hashlib
        import hmac
        body      = await request.body()
        signature = request.headers.get("X-Hub-Signature-256", "")
        expected  = "sha256=" + hmac.new(
            secret.get_secret_value().encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature.",
            )

    payload    = await request.json()
    event_type = request.headers.get("X-GitHub-Event", "")

    # Only act on pull_request opened/synchronize events
    if event_type != "pull_request":
        return {"status": "ignored", "reason": f"event type '{event_type}' not handled"}

    action  = payload.get("action", "")
    if action not in ("opened", "synchronize", "reopened"):
        return {"status": "ignored", "reason": f"action '{action}' not handled"}

    pr_data = payload.get("pull_request", {})
    pr_url  = pr_data.get("html_url", "")
    if not pr_url:
        return {"status": "ignored", "reason": "no PR URL in payload"}

    # Trigger analysis asynchronously (fire-and-forget)
    import asyncio
    asyncio.create_task(_background_analyse(pr_url))

    return {"status": "accepted", "pr_url": pr_url}


async def _background_analyse(pr_url: str) -> None:
    """Run analysis in the background — errors are logged, not raised."""
    try:
        service = AnalysisService()
        result  = await service.analyse(pr_url=pr_url)
        _result_cache[result.analysis_id] = result
        logger.info(
            "Background analysis complete: %s → %s",
            pr_url, result.verdict,
        )
    except Exception as exc:
        logger.error("Background analysis failed for %s: %s", pr_url, exc, exc_info=True)
