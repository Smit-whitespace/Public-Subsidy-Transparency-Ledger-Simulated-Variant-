"""
backend/main.py

Application entrypoint and app factory for the FastAPI service.
Static router registration (no dynamic imports).
"""

from typing import List
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.config import settings
from backend.utils.logging import configure_logging, get_logger
from backend.utils.exceptions import register_exception_handlers
from backend.utils.response import success_response

# --- AUTH (FIXED: moved to core layer) ---
from backend.core.security import get_current_user

# --- STATIC ROUTER IMPORTS ---
from backend.routes.health import router as health_router
from backend.routes.auth_routes import router as auth_router
from backend.routes.subsidy_routes import router as subsidy_router
from backend.routes.project_routes import router as project_router
from backend.routes.disbursement_routes import router as disbursement_router
from backend.routes.audit_routes import router as audit_router
from backend.routes.search_routes import router as search_router
from backend.routes.analytics_routes import router as analytics_router
from backend.routes.admin_routes import router as admin_router
from backend.routes.risk_event_routes import router as risk_event_router

logger = get_logger(__name__)


# ============================================================
# CORS CONFIGURATION
# ============================================================

def _parse_cors_origins() -> List[str]:
    if settings.ALLOW_ORIGINS:
        origins = [origin.strip() for origin in settings.ALLOW_ORIGINS.split(",")]
        return [o for o in origins if o]

    if settings.ENVIRONMENT == "production":
        return []

    return ["*"]


# ============================================================
# APP FACTORY
# ============================================================

def create_app() -> FastAPI:
    configure_logging()
    logger.info(f"Creating FastAPI application: {settings.APP_NAME}")

    app = FastAPI(
        title=settings.APP_NAME,
        docs_url="/docs",
        redoc_url="/redoc",
        version="v1"
    )

    # --------------------------------------------------------
    # CORS
    # --------------------------------------------------------

    allowed_origins = _parse_cors_origins()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    # --------------------------------------------------------
    # Exception Handlers
    # --------------------------------------------------------

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
    # STATIC ROUTER REGISTRATION
    # ============================================================

    # Public routes
    app.include_router(health_router, prefix="/health")
    app.include_router(auth_router, prefix="/auth")

    # Protected routes (require authentication)
    auth_dependency = [Depends(get_current_user)]

    app.include_router(subsidy_router, prefix="/subsidies", dependencies=auth_dependency)
    app.include_router(project_router, prefix="/projects", dependencies=auth_dependency)
    app.include_router(disbursement_router, prefix="/disbursements", dependencies=auth_dependency)
    app.include_router(audit_router, prefix="/audits", dependencies=auth_dependency)
    app.include_router(search_router, prefix="/search", dependencies=auth_dependency)
    app.include_router(analytics_router, dependencies=auth_dependency)
    app.include_router(admin_router, dependencies=auth_dependency)
    app.include_router(risk_event_router, dependencies=auth_dependency)

    logger.info("All routers registered statically")

    # ============================================================
    # ROOT
    # ============================================================

    @app.get("/", tags=["root"])
    async def root():
        return success_response({
            "app": settings.APP_NAME,
            "status": "ok",
            "env": settings.ENVIRONMENT
        })

    # ============================================================
    # STARTUP
    # ============================================================

    @app.on_event("startup")
    async def startup_event():
        logger.info(f"Application starting - Environment: {settings.ENVIRONMENT}")

        try:
            from backend.database.connection import engine, Base, SessionLocal
            from backend.seed.seed_roles import seed_roles

            # Connectivity check
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            logger.info("Database connectivity check: OK")

            # Ensure tables exist
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created/ensured")

            # Auto role seeding
            db = SessionLocal()
            try:
                seed_roles(db)
                logger.info("Default roles seeded")
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")

        logger.info("Application startup complete")

    # ============================================================
    # SHUTDOWN
    # ============================================================

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


# ============================================================
# APP INSTANCE
# ============================================================

app = create_app()


# ============================================================
# LOCAL DEVELOPMENT RUNNER
# ============================================================

if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.getenv("PORT", "8000"))
    reload = settings.ENVIRONMENT != "production"

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=reload
    )


__all__ = ["create_app", "app"]