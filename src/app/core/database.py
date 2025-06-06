# File: src/app/core/database.py
"""
This module contains the database connection and session management code.
It uses SQLAlchemy as the ORM and asynchronous connections to a PostgreSQL database.
"""

from __future__ import annotations
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base 
from src.app.core.config import settings

# Base class for declarative models
Base = declarative_base()

# Create the SQLAlchemy engine using the database URI from settings
engine = create_async_engine(
    url=str(settings.DATABASE_URI),
    # Log SQL statements for debugging
    echo=True,
    # Pool size
    pool_size=5,
    # The size of the pool to be maintained, or None for unbounded pool size
    max_overflow=10,
)
# Dependency for getting a DB session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides an async SQLAlchemy session for dependency injection.

    Yields:
        AsyncSession: An instance of SQLAlchemy async session.
    """
    # Async session factory
    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,  # Type of session to create
        autocommit=False,  # Don't commit automatically
        expire_on_commit=False,
    )
    async with async_session() as session:
        yield session
