"""
backend/routes/health.py

Health and readiness check endpoints for the subsidy management system.

This module provides lightweight monitoring endpoints that external systems (load balancers,
orchestrators like Kubernetes, monitoring tools) can use to determine if the application is
alive and ready to serve traffic. The endpoints perform minimal checks to avoid impacting
application performance while still providing meaningful health signals.

The /ping endpoint is a simple liveness check that always returns success if the application
process is running. The /ready endpoint performs actual dependency checks (database, redis,
blockchain RPC) to determine if the application can handle requests. The /meta endpoint
provides basic application metadata for debugging and monitoring purposes.

Test the health endpoints with curl:
    curl http://localhost:8000/api/health/ping
    curl http://localhost:8000/api/health/ready
"""

import json
from typing import Any, Dict
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.config import settings
from backend.database.connection import engine


router = APIRouter( tags=["health"])


def _mask_connection_string(url: str) -> str:
    """
    Mask sensitive information in a connection string URL.
    
    This function parses a URL and returns a sanitized version that includes only the scheme
    and network location (host:port), stripping out usernames, passwords, paths, and query
    parameters. This is essential for health check endpoints that need to report configuration
    without exposing credentials in logs or monitoring systems.
    
    Args:
        url: The connection string URL to mask
    
    Returns:
        A masked version like "postgresql://db-host:5432" or "http://rpc.example.com"
    """
    if not url:
        return "<not configured>"
    
    try:
        parsed = urlparse(url)
        # Reconstruct with only scheme and netloc (host:port), dropping userinfo and path/query
        masked = urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))
        return masked
    except Exception:
        return "<invalid url>"


def _check_database() -> Dict[str, Any]:
    """
    Check database connectivity by executing a simple test query.
    
    This performs a lightweight SELECT 1 query to verify that the database is reachable and
    accepting connections. We use a raw connection context rather than a full ORM session to
    minimize overhead, making this suitable for frequent health checks without impacting
    application performance.
    
    Returns:
        A dictionary with 'ok' (bool) and 'detail' (str) keys describing the check result
    """
    try:
        # Use a connection context from the engine pool. This is lightweight and doesn't
        # involve ORM overhead. The context manager ensures the connection is returned to
        # the pool even if an error occurs.
        with engine.connect() as conn:
            # Execute a simple query that every SQL database supports. This verifies that
            # the connection is working and the database can process queries. Using text()
            # for explicit SQL string handling as recommended by SQLAlchemy 2.0 patterns.
            result = conn.execute(text("SELECT 1"))
            # Fetch one row to ensure the query actually executed successfully
            result.fetchone()
            
        return {"ok": True, "detail": "Database connection successful"}
        
    except SQLAlchemyError as e:
        # Database connectivity or query execution failed. This is the most critical failure
        # mode as the application can't function without database access.
        return {"ok": False, "detail": f"Database error: {str(e)}"}
        
    except Exception as e:
        # Catch any other unexpected errors during the database check to prevent the health
        # endpoint itself from crashing. This ensures monitoring systems always get a response.
        return {"ok": False, "detail": f"Unexpected error: {str(e)}"}


def _check_redis() -> Dict[str, Any]:
    """
    Check Redis connectivity if Redis is configured and available.
    
    This optional check attempts to import the redis library and ping a Redis server if a
    connection URL is configured. Redis is commonly used for caching and sessions, but not
    all deployments require it, so this check gracefully handles its absence.
    
    Returns:
        A dictionary with 'ok' (bool) and 'detail' (str) keys describing the check result
    """
    # Check if Redis URL is configured in settings. If not, skip the check entirely.
    redis_url = getattr(settings, "REDIS_URL", None)
    if not redis_url:
        return {"ok": True, "detail": "Redis not configured (skipped)"}
    
    try:
        # Attempt to import redis. If the package isn't installed, we can't perform the check.
        import redis
        
        # Create a Redis client with a short timeout to avoid blocking health checks for too
        # long if Redis is slow or unreachable. The socket timeouts ensure we fail fast.
        client = redis.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2)
        
        # Ping the Redis server. This is the minimal operation to verify connectivity.
        client.ping()
        
        return {"ok": True, "detail": "Redis connection successful"}
        
    except ImportError:
        # Redis library isn't installed. This is fine if Redis isn't actually needed, but we
        # report it as skipped rather than failed since the configuration suggests it should
        # be available.
        return {"ok": True, "detail": "Redis library not installed (skipped)"}
        
    except redis.exceptions.RedisError as e:
        # Redis is configured and the library is available, but connection or ping failed.
        # This indicates a real problem with the Redis dependency.
        return {"ok": False, "detail": f"Redis error: {str(e)}"}
        
    except Exception as e:
        # Catch any other unexpected errors during the Redis check to prevent crashes.
        return {"ok": False, "detail": f"Unexpected error: {str(e)}"}


def _check_blockchain_rpc() -> Dict[str, Any]:
    """
    Check blockchain RPC endpoint connectivity if configured.
    
    This optional check attempts a minimal JSON-RPC call to the configured blockchain endpoint
    to verify it's reachable and responding. The check uses a standard web3_clientVersion
    method that most Ethereum-compatible RPC providers support, though the exact response
    format isn't critical - we just need to verify the endpoint is alive.
    
    Returns:
        A dictionary with 'ok' (bool) and 'detail' (str) keys describing the check result
    """
    # Check if blockchain RPC URL is configured. If not, skip this check.
    rpc_url = getattr(settings, "BLOCKCHAIN_RPC", None)
    if not rpc_url or not rpc_url.strip():
        return {"ok": True, "detail": "Blockchain RPC not configured (skipped)"}
    
    try:
        # Construct a minimal JSON-RPC request. We use web3_clientVersion which is a standard
        # method that returns the client software version and is supported by most providers.
        # This is a read-only method that doesn't modify any state.
        rpc_request = {
            "jsonrpc": "2.0",
            "method": "web3_clientVersion",
            "params": [],
            "id": 1
        }
        
        # Create the HTTP request with appropriate headers and a short timeout. The timeout
        # ensures we don't block health checks indefinitely if the RPC endpoint is unreachable.
        request = Request(
            rpc_url,
            data=json.dumps(rpc_request).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        
        # Execute the request with a 5-second timeout. This is generous enough for most RPC
        # providers but short enough to fail fast if there's a connectivity issue.
        with urlopen(request, timeout=5) as response:
            # Check if we got a successful HTTP response. We don't validate the JSON-RPC
            # response format because different providers may return different structures,
            # but getting a 200 OK is sufficient to know the endpoint is alive.
            if response.status == 200:
                return {"ok": True, "detail": "Blockchain RPC connection successful"}
            else:
                return {"ok": False, "detail": f"Unexpected HTTP status: {response.status}"}
        
    except HTTPError as e:
        # HTTP error (4xx, 5xx) from the RPC endpoint. This indicates the endpoint is reachable
        # but returned an error response, which we treat as a failure.
        return {"ok": False, "detail": f"HTTP error: {e.code} {e.reason}"}
        
    except URLError as e:
        # Network error (DNS failure, connection refused, timeout, etc.). This indicates the
        # RPC endpoint is unreachable.
        return {"ok": False, "detail": f"Connection error: {str(e.reason)}"}
        
    except Exception as e:
        # Catch any other unexpected errors during the RPC check to prevent crashes.
        return {"ok": False, "detail": f"Unexpected error: {str(e)}"}


@router.get("/ping")
def ping() -> Dict[str, str]:
    """
    Simple liveness check endpoint.
    
    This endpoint always returns success if the application process is running and can handle
    HTTP requests. It performs no dependency checks and is designed to be as fast and lightweight
    as possible. Load balancers and orchestrators use this to determine if the application
    process should be restarted.
    
    Returns:
        A simple success message indicating the application is alive
    """
    return {"status": "ok", "message": "pong"}


@router.get("/ready")
def ready() -> JSONResponse:
    """
    Readiness check endpoint that verifies critical dependencies.
    
    This endpoint performs actual checks of the application's dependencies (database, redis,
    blockchain RPC) to determine if it's ready to serve traffic. Unlike the liveness check,
    this can fail if dependencies are unavailable, which tells load balancers and orchestrators
    to stop routing traffic to this instance until it recovers.
    
    The check logic distinguishes between critical failures (database unavailable) and degraded
    states (optional services unavailable). This allows for graceful degradation where the
    application can continue serving some requests even if non-critical dependencies fail.
    
    Returns:
        A JSON response with overall status and detailed check results. Returns HTTP 200 for
        ok/degraded states and HTTP 503 for critical failures.
    """
    # Perform all dependency checks. Each check is independent and returns its own result.
    checks = {
        "db": _check_database(),
        "redis": _check_redis(),
        "blockchain_rpc": _check_blockchain_rpc(),
    }
    
    # Determine the overall application status based on check results. The database is the
    # only truly critical dependency - if it's down, we can't function at all.
    db_ok = checks["db"]["ok"]
    redis_ok = checks["redis"]["ok"]
    rpc_ok = checks["blockchain_rpc"]["ok"]
    
    if not db_ok:
        # Database is down - this is a critical failure. Return HTTP 503 to tell load balancers
        # to stop routing traffic here and potentially restart the application.
        overall_status = "fail"
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE
    elif not redis_ok or not rpc_ok:
        # Database is up but optional dependencies are failing. We're in a degraded state where
        # we can serve some requests but not all functionality is available. Still return 200
        # to keep receiving traffic since core functionality works.
        overall_status = "degraded"
        http_status = status.HTTP_200_OK
    else:
        # All checks passed - everything is working normally.
        overall_status = "ok"
        http_status = status.HTTP_200_OK
    
    # Construct the response with overall status and detailed check results. This gives
    # operators visibility into exactly what's failing when troubleshooting issues.
    response_data = {
        "status": overall_status,
        "checks": checks,
    }
    
    return JSONResponse(status_code=http_status, content=response_data)


@router.get("/meta")
def meta() -> Dict[str, str]:
    """
    Return application metadata for debugging and monitoring.
    
    This endpoint provides basic information about the running application including its name,
    version, and masked configuration values. The configuration URLs are masked to prevent
    leaking credentials in logs or monitoring dashboards while still providing enough information
    to verify that the application is configured correctly.
    
    Returns:
        A dictionary containing application name, version, and masked configuration URLs
    """
    # Get the application name from settings, with a sensible default if not configured.
    app_name = getattr(settings, "APP_NAME", "Subsidy Management System")
    
    # Get configuration URLs and mask any sensitive information like credentials or API keys.
    # This allows operators to verify configuration without exposing secrets.
    database_url = getattr(settings, "DATABASE_URL", "")
    blockchain_rpc = getattr(settings, "BLOCKCHAIN_RPC", "")
    
    return {
        "app": app_name,
        "database_url": _mask_connection_string(database_url),
        "blockchain_rpc": _mask_connection_string(blockchain_rpc),
        "version": "v1",
    }