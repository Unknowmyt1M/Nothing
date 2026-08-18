"""UpDownVid FastAPI application factory.

Builds the ASGI app with CORS, signed-cookie sessions (Starlette), and all
API routers. Keeps the same URL contracts the frontend expects.
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from backend.config import (
    SESSION_SECRET,
    CORS_ORIGINS,
    FRONTEND_URL,
    IS_PRODUCTION,
    DEBUG,
)
from backend.errors import AppError
from backend.database.json_db import database_init
from backend.services.downloader_service import start_cleanup_thread

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown hooks."""
    # 1. Initialize local JSON database directory (safe, idempotent)
    try:
        database_init()
    except Exception as e:  # pragma: no cover - defensive
        logger.critical("Failed to initialize database: %s", e)

    # 2. Start background cleanup thread
    start_cleanup_thread()

    yield
    logger.info("Backend shutdown complete")


def create_app() -> FastAPI:
    """Application factory to configure and initialize FastAPI."""
    app = FastAPI(
        title="UpDownVid Backend API",
        description="Unified video downloader & uploader platform backend",
        version="2.0.0",
        lifespan=lifespan,
    )

    # Signed-cookie sessions so /api/auth/* can persist login like Flask did
    # Production: cross-origin (Vercel → Render) needs same_site="none" + https_only
    session_kwargs = (
        {"same_site": "none", "https_only": True}
        if IS_PRODUCTION
        else {"same_site": "lax", "https_only": False}
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=SESSION_SECRET,
        **session_kwargs,
    )

    # CORS: allow the Next.js dashboard + local API origin
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routers (Flask blueprint equivalents)
    from backend.api.auth_routes import router as auth_router
    from backend.api.downloader_routes import router as downloader_router
    from backend.api.automation_routes import router as automation_router
    from backend.api.debug_routes import router as debug_router
    from backend.api.analytics_routes import router as analytics_router

    app.include_router(auth_router, prefix="/api")
    app.include_router(downloader_router, prefix="/api")
    app.include_router(automation_router, prefix="/api")
    if DEBUG or not IS_PRODUCTION:
        app.include_router(debug_router, prefix="/api")
    app.include_router(analytics_router, prefix="/api")

    # Global handler for structured errors
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(exc.to_dict(), status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        logger.error("Unhandled error: %s", exc, exc_info=True)
        return JSONResponse(
            {"error": True, "code": "UNKNOWN_ERROR", "title": "Something went wrong",
             "message": "An unexpected error occurred.", "retryable": True},
            status_code=500,
        )

    @app.get("/")
    async def index():
        """Redirect root access to the Next.js dashboard."""
        return RedirectResponse(FRONTEND_URL)

    @app.get("/healthz")
    async def health_check():
        return JSONResponse({"status": "healthy", "database": "JSON Storage Active"})

    @app.get("/docs", include_in_schema=False)
    @app.get("/redoc", include_in_schema=False)
    async def docs_redirect(request: Request):
        """Keep openapi docs accessible at /docs even when proxied."""
        return JSONResponse({"docs": "/docs"})

    return app


app = create_app()