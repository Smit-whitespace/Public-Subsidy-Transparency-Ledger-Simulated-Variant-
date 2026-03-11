"""
backend/database/connection.py

Central database configuration module for the FastAPI application using synchronous SQLAlchemy.

This module establishes the database engine, session factory, and declarative base that all
models inherit from. It provides a FastAPI dependency for injecting database sessions into
route handlers with proper cleanup and error handling.

The default setup uses synchronous SQLAlchemy, which is simpler to reason about and sufficient
for most use cases. An async configuration example is included as comments for teams that need
it in the future.

Key exports:
- engine: The SQLAlchemy Engine instance connected to your database
- SessionLocal: Session factory for creating new database sessions
- Base: Declarative base class that all ORM models should inherit from
- get_db(): FastAPI dependency that yields a database session with automatic cleanup
- init_db(): Helper function for creating tables during development/testing
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# Import application settings which include DATABASE_URL and other configuration.
# The settings object is typically loaded from environment variables using Pydantic.
from backend.config import settings


__all__ = ["engine", "SessionLocal", "Base", "get_db", "init_db"]


# Detect if we're using SQLite and need to disable the same-thread check. SQLite by default
# restricts connections to the thread that created them, but SQLAlchemy's connection pooling
# can safely share connections across threads in most scenarios. We enable this only for
# SQLite to avoid adding unnecessary kwargs for PostgreSQL, MySQL, etc.
connect_args = {}
if "sqlite" in str(settings.DATABASE_URL).lower():
    connect_args["check_same_thread"] = False
    # TODO: Replace SQLite with PostgreSQL or another production database for deployment


# Create the synchronous engine that manages database connections. The echo parameter can
# be enabled during development to see SQL queries logged to the console, which is helpful
# for debugging but should be disabled in production to avoid log noise.
engine: Engine = create_engine(
    str(settings.DATABASE_URL),
    connect_args=connect_args,
    echo=False,  # Set to True during development if you want to see SQL queries
    pool_pre_ping=True,  # Verify connections are alive before using them from the pool
)


# Configure the session factory with sensible defaults for a web application. We disable
# autocommit because explicit commits give you better control over transaction boundaries.
# We also disable autoflush to prevent SQLAlchemy from issuing unexpected SQL during query
# operations, making behavior more predictable.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# Create the declarative base class that all ORM models will inherit from. This Base tracks
# all model metadata and is used by Alembic for migration autogeneration. When setting up
# Alembic, configure env.py to import this Base and set target_metadata = Base.metadata.
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session to route handlers.
    
    This generator-based dependency creates a new session for each request, yields it to
    the route handler, and ensures proper cleanup regardless of whether the request succeeds
    or fails. The session is automatically rolled back on exceptions to prevent partial
    commits, and always closed in the finally block to return the connection to the pool.
    
    Usage in FastAPI routes:
        @app.get("/users")
        def list_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    
    The rollback-on-exception behavior ensures that if your route handler raises an error
    (validation failure, business logic exception, etc.), any database changes are discarded
    rather than being accidentally committed. This prevents data corruption and maintains
    transaction integrity.
    
    Yields:
        A SQLAlchemy Session instance bound to the application's database engine.
    """
    # Create a new session from our configured factory. This session is independent and
    # can be used safely throughout the request lifecycle without interfering with other
    # concurrent requests.
    db = SessionLocal()
    
    try:
        # Yield the session to the route handler. Control returns here after the route
        # completes (either successfully or with an exception).
        yield db
    except SQLAlchemyError as exc:
        # If a database-level error occurs (connection issues, constraint violations, etc.),
        # we roll back any pending changes to keep the database in a consistent state.
        db.rollback()
        raise exc
    except Exception as exc:
        # For any other exception (business logic errors, validation failures, etc.), we
        # also roll back to ensure partial changes aren't committed. This is a safety net
        # that prevents subtle bugs where half a transaction succeeds.
        db.rollback()
        raise exc
    finally:
        # Always close the session to release the database connection back to the pool,
        # regardless of success or failure. This prevents connection leaks that would
        # eventually exhaust the pool and cause the application to hang.
        db.close()


def init_db(engine_obj: Engine | None = None) -> list[str]:
    """
    Create all tables defined in Base.metadata in the target database.
    
    This function is useful for local development, integration tests, or initial deployment
    when you want to quickly set up the database schema. It's idempotent and safe to call
    multiple times because SQLAlchemy only creates tables that don't already exist.
    
    Important: In production environments, use Alembic migrations instead of this function.
    Alembic provides version control for your schema, allows incremental updates, and creates
    an audit trail of how your database structure evolved. To configure Alembic, import this
    module's Base in alembic/env.py and set target_metadata = Base.metadata.
    
    Args:
        engine_obj: Optional SQLAlchemy Engine to use for table creation. If not provided,
                    uses the module-level engine. Passing a custom engine is useful for
                    testing with temporary databases.
    
    Returns:
        A list of table names that are now present in Base.metadata. This includes both
        newly created tables and tables that already existed. Useful for verification and
        debugging when tables mysteriously don't appear (usually because their model class
        wasn't imported yet).
    """
    # Use the provided engine or fall back to the module's default engine. This flexibility
    # lets you call init_db with a test database engine during pytest runs.
    target_engine = engine_obj or engine
    
    # The create_all method inspects Base.metadata for all registered Table objects and
    # issues CREATE TABLE statements for any that don't exist. It won't modify or drop
    # existing tables, making it safe for incremental development.
    Base.metadata.create_all(bind=target_engine)
    
    # Return the list of table names so callers can verify what got created. This is
    # especially helpful in test scenarios or when debugging model registration issues.
    return list(Base.metadata.tables.keys())


# ============================================================================
# ASYNC CONFIGURATION (Optional - commented out by default)
# ============================================================================
# If your application needs asynchronous database operations (e.g., you're using async
# route handlers and want to avoid blocking the event loop), uncomment and configure
# the following async setup. Note that async adds complexity and isn't always necessary;
# synchronous SQLAlchemy with a connection pool handles most workloads efficiently.
#
# from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
# from sqlalchemy.ext.asyncio import async_sessionmaker
#
# # Create an async engine. Note the database URL must use an async driver like
# # asyncpg for PostgreSQL (postgresql+asyncpg://...) or aiosqlite for SQLite.
# async_engine = create_async_engine(
#     settings.ASYNC_DATABASE_URL,  # You'd need to add this to your settings
#     echo=False,
#     pool_pre_ping=True,
# )
#
# # Create an async session factory. Note the use of async_sessionmaker instead of
# # the regular sessionmaker, and the class_=AsyncSession parameter.
# AsyncSessionLocal = async_sessionmaker(
#     autocommit=False,
#     autoflush=False,
#     bind=async_engine,
#     class_=AsyncSession,
#     expire_on_commit=False,  # Prevents lazy-loading errors after commit
# )
#
# async def get_async_db() -> Generator[AsyncSession, None, None]:
#     """
#     Async version of get_db() for use with async route handlers.
#     
#     Usage:
#         @app.get("/users")
#         async def list_users(db: AsyncSession = Depends(get_async_db)):
#             result = await db.execute(select(User))
#             return result.scalars().all()
#     """
#     async with AsyncSessionLocal() as session:
#         try:
#             yield session
#             await session.commit()
#         except Exception:
#             await session.rollback()
#             raise
# ============================================================================


# This standalone execution block is useful for quickly setting up a development database
# or verifying that your models are properly registered. Running this file directly with
# "python -m backend.database.connection" will create all tables and print their names.
if __name__ == "__main__":
    print("Initializing database and creating tables...")
    print(f"Database URL: {settings.DATABASE_URL}\n")
    
    # Call init_db to create tables. This is safe to run multiple times because it only
    # creates tables that don't already exist, never modifying or dropping existing ones.
    table_names = init_db()
    
    if table_names:
        print(f"Successfully verified {len(table_names)} table(s) in the database:")
        for table_name in table_names:
            print(f"  - {table_name}")
    else:
        print("Warning: No tables found in Base.metadata!")
        print("\nThis usually means your model classes haven't been imported yet.")
        print("Make sure to import all models before calling init_db():")
        print("  from backend.models.user import User")
        print("  from backend.models.subsidy import Subsidy")
        print("  from backend.models.audit import AuditRecord")
    
    print("\n✓ Database initialization complete")
    
    # Testing tip: To test get_db() in pytest, you can monkeypatch settings.DATABASE_URL
    # to use an in-memory SQLite database, then call init_db() and use get_db() in your
    # test fixtures. Example:
    #   monkeypatch.setattr("backend.config.settings.DATABASE_URL", "sqlite:///:memory:")