"""
backend/main.py

Application entrypoint and app factory for the FastAPI service.
"""

from typing import List, Optional
import importlib
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.utils.logging import configure_logging, get_logger
from backend.utils.exceptions import register_exception_handlers, AppError, to_http_exception
from backend.utils.response import success_response


# Configure module logger
logger = get_logger(__name__)


def _get_prefix(route_name: str) -> str:
    """
    Map route module name to URL prefix.
    
    Args:
        route_name: Name of route module
    
    Returns:
        URL prefix string
    """
    prefix_map = {
        "health": "/health",
        "auth_routes": "/auth",
        "subsidy_routes": "/subsidies",
        "project_routes": "/projects",
        "disbursement_routes": "/disbursements",
        "audit_routes": "/audits",
        "search_routes": "/search"
    }
    return prefix_map.get(route_name, f"/{route_name}")


def _parse_cors_origins() -> List[str]:
    """
    Parse CORS origins from settings.
    
    Returns comma-separated origins from ALLOW_ORIGINS setting, or default list.
    In production, defaults to empty list (no open CORS); in dev, allows all.
    
    Returns:
        List of allowed origin strings
    """
    if settings.ALLOW_ORIGINS:
        # Parse comma-separated origins
        origins = [origin.strip() for origin in settings.ALLOW_ORIGINS.split(",")]
        return [o for o in origins if o]  # Filter empty strings
    
    # Default CORS policy based on environment
    if settings.ENVIRONMENT == "production":
        # Restrictive in production - no origins allowed by default
        return []
    else:
        # Permissive in development
        return ["*"]


def create_app() -> FastAPI:
    """
    Application factory for FastAPI service.
    
    Configures logging, middleware, exception handlers, routers, and lifecycle events.
    Creates a fresh FastAPI instance each time called.
    
    Returns:
        Configured FastAPI application instance
    """
    # Configure logging first
    configure_logging()
    logger.info(f"Creating FastAPI application: {settings.APP_NAME}")
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.APP_NAME,
        docs_url="/docs",
        redoc_url="/redoc",
        version="v1"
    )
    
    # Configure CORS middleware
    allowed_origins = _parse_cors_origins()
    logger.info(f"Configuring CORS with origins: {allowed_origins}")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    
    # Register custom exception handlers
    # Converts AppError and subclasses to proper HTTP responses
    register_exception_handlers(app)
    
    # Add fallback exception handler for production
    # In production, catch all unhandled exceptions and return safe error
    # In development, let FastAPI's default error handling show debug info
    if settings.ENVIRONMENT == "production":
        @app.exception_handler(Exception)
        async def production_exception_handler(request: Request, exc: Exception):
            """Catch-all exception handler for production - logs and returns safe error."""
            logger.error(f"Unhandled exception: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": "Internal server error"
                }
            )
    
    # Include routers safely - tolerate missing modules
    route_modules = [
        "health",
        "auth_routes",
        "subsidy_routes",
        "project_routes",
        "disbursement_routes",
        "audit_routes",
        "search_routes"
    ]
    
    for module_name in route_modules:
        try:
            module = importlib.import_module(f"backend.routes.{module_name}")
            if hasattr(module, "router"):
                prefix = _get_prefix(module_name)
                app.include_router(module.router, prefix=prefix)
                logger.info(f"Registered router: {module_name} at {prefix}")
            else:
                logger.warning(f"Module {module_name} has no 'router' attribute")
        except ImportError as e:
            logger.warning(f"Could not import route module {module_name}: {e}")
        except Exception as e:
            logger.error(f"Error registering router {module_name}: {e}")
    
    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint returning application status."""
        return success_response({
            "app": settings.APP_NAME,
            "status": "ok",
            "env": settings.ENVIRONMENT
        })
    
    # Startup event handler
    @app.on_event("startup")
    async def startup_event():
        """
        Application startup handler.
        
        Performs lightweight checks and logs configuration.
        Does not block startup on failed checks.
        """
        logger.info(f"Application starting - Environment: {settings.ENVIRONMENT}")
        
        # Attempt lightweight DB connectivity check
        try:
            from backend.database.connection import engine
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            logger.info("Database connectivity check: OK")
        except ImportError:
            logger.warning("Database connection module not available")
        except Exception as e:
            logger.error(f"Database connectivity check failed: {e}")
        
        # Log external service configuration status
        if settings.REDIS_URL:
            logger.info(f"Redis configured: {settings.REDIS_URL[:20]}...")
        
        if settings.BLOCKCHAIN_RPC:
            logger.info(f"Blockchain RPC configured: {settings.BLOCKCHAIN_RPC[:30]}...")
        
        if settings.SENTRY_DSN:
            logger.info("Sentry DSN configured")
        
        logger.info("Application startup complete")
    
    # Shutdown event handler
    @app.on_event("shutdown")
    async def shutdown_event():
        """
        Application shutdown handler.
        
        Gracefully closes resources and connections.
        """
        logger.info("Application shutting down")
        
        # Dispose database engine
        try:
            from backend.database.connection import engine
            engine.dispose()
            logger.info("Database engine disposed")
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"Error disposing database engine: {e}")
        
        logger.info("Application shutdown complete")
    
    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    """
    Direct execution entry point.
    
    Runs the application using uvicorn when executed directly.
    Not recommended for production - use a proper ASGI server.
    """
    try:
        import uvicorn
        import os
    except ImportError:
        raise RuntimeError(
            "uvicorn is required to run the app directly. "
            "Install 'uvicorn[standard]' or run with an ASGI server."
        )
    
    # Get port from environment or use default
    port = int(os.getenv("PORT", "8000"))
    
    # Enable reload in non-production environments
    reload = settings.ENVIRONMENT != "production"
    
    logger.info(f"Starting uvicorn server on port {port} (reload={reload})")
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=reload
    )


__all__ = ["create_app", "app"]

# Test hint: import create_app and call TestClient(create_app()) to exercise routes and startup/shutdown handlers in tests.