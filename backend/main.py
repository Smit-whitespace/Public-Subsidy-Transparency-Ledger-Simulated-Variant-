"""
backend/main.py

Application entrypoint and app factory for the FastAPI service.
Static router registration (no dynamic imports).
"""

from typing import List
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.config import settings
from backend.utils.logging import configure_logging, get_logger
from backend.utils.exceptions import register_exception_handlers
from backend.utils.response import success_response

# --- STATIC ROUTER IMPORTS (CRITICAL FIX) ---
from backend.routes.health import router as health_router
from backend.routes.auth_routes import router as auth_router
from backend.routes.subsidy_routes import router as subsidy_router
from backend.routes.project_routes import router as project_router
from backend.routes.disbursement_routes import router as disbursement_router
from backend.routes.audit_routes import router as audit_router
from backend.routes.search_routes import router as search_router


logger = get_logger(__name__)


def _parse_cors_origins() -> List[str]:
    if settings.ALLOW_ORIGINS:
        origins = [origin.strip() for origin in settings.ALLOW_ORIGINS.split(",")]
        return [o for o in origins if o]

    if settings.ENVIRONMENT == "production":
        return []

    return ["*"]


def create_app() -> FastAPI:
    configure_logging()
    logger.info(f"Creating FastAPI application: {settings.APP_NAME}")

    app = FastAPI(
        title=settings.APP_NAME,
        docs_url="/docs",
        redoc_url="/redoc",
        version="v1"
    )

    # --- CORS ---
    allowed_origins = _parse_cors_origins()
    logger.info(f"Configuring CORS with origins: {allowed_origins}")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    # --- Exception Handlers ---
    register_exception_handlers(app)

    if settings.ENVIRONMENT == "production":
        @app.exception_handler(Exception)
        async def production_exception_handler(request: Request, exc: Exception):
            logger.error(f"Unhandled exception: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": "Internal server error"
                }
            )

    # ============================================================
    # STATIC ROUTER REGISTRATION (NO DYNAMIC IMPORTS)
    # ============================================================

    app.include_router(health_router, prefix="/health")
    app.include_router(auth_router, prefix="/auth")
    app.include_router(subsidy_router, prefix="/subsidies")
    app.include_router(project_router, prefix="/projects")
    app.include_router(disbursement_router, prefix="/disbursements")
    app.include_router(audit_router, prefix="/audits")
    app.include_router(search_router, prefix="/search")

    logger.info("All routers registered statically")

    # --- Root ---
    @app.get("/", tags=["root"])
    async def root():
        return success_response({
            "app": settings.APP_NAME,
            "status": "ok",
            "env": settings.ENVIRONMENT
        })

    # --- Startup ---
    @app.on_event("startup")
    async def startup_event():
        logger.info(f"Application starting - Environment: {settings.ENVIRONMENT}")

        try:
            from backend.database.connection import engine
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connectivity check: OK")
        except Exception as e:
            logger.error(f"Database connectivity check failed: {e}")

        logger.info("Application startup complete")

    # --- Shutdown ---
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Application shutting down")

        try:
            from backend.database.connection import engine
            engine.dispose()
            logger.info("Database engine disposed")
        except Exception as e:
            logger.error(f"Error disposing database engine: {e}")

        logger.info("Application shutdown complete")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.getenv("PORT", "8000"))
    reload = settings.ENVIRONMENT != "production"

    logger.info(f"Starting uvicorn server on port {port} (reload={reload})")

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=reload
    )


__all__ = ["create_app", "app"]
