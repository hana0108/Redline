from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Set search_path via PostgreSQL server-side connection option.
# This is the most reliable approach with psycopg3: it is applied before
# any transaction starts, supersedes event-listener timing issues, and
# persists for the full session without relying on SQLAlchemy events.
_connect_args: dict = {}
if settings.DATABASE_SCHEMA:
    _connect_args = {"options": f"-csearch_path={settings.DATABASE_SCHEMA},public"}

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
