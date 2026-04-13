from __future__ import annotations

from pathlib import Path

from sqlalchemy import inspect

from app.core.config import settings
from app.db.seed_auth import run as seed_auth_run
from app.db.session import engine


def _project_root() -> Path:
    here = Path(__file__).resolve()
    return here.parents[3]


def _execute_sql_file(sql_path: Path) -> None:
    """Execute a .sql file that manages its own BEGIN/COMMIT transaction.

    psycopg3 starts an implicit transaction on the first execute() call
    (auto-begin).  That conflicts with the explicit BEGIN inside our SQL
    files and causes psycopg3's internal transaction-state to desync.
    Setting autocommit=True on the underlying DBAPI connection before
    executing lets the SQL file control the transaction itself.
    """
    sql_text = sql_path.read_text(encoding="utf-8")
    raw = engine.raw_connection()
    try:
        # raw.driver_connection is the actual psycopg3 Connection object.
        # autocommit can be changed when the connection is idle (which it
        # always is right after pool checkout with pool_pre_ping=True).
        dbapi_conn = raw.driver_connection
        dbapi_conn.autocommit = True
        try:
            with dbapi_conn.cursor() as cur:
                cur.execute(sql_text)
        finally:
            dbapi_conn.autocommit = False
    finally:
        raw.close()


def _schema_ready() -> bool:
    schema = settings.DATABASE_SCHEMA
    inspector = inspect(engine)
    return (
        inspector.has_table("users", schema=schema)
        and inspector.has_table("roles", schema=schema)
        and inspector.has_table("vehicle_brands", schema=schema)
        and inspector.has_table("vehicle_models_catalog", schema=schema)
    )


def bootstrap_database() -> None:
    root = _project_root()
    schema_sql = root / "database" / "redline_schema.sql"
    vehicle_catalogs_seed_sql = root / "database" / "seed_vehicle_catalogs.sql"

    if not _schema_ready():
        _execute_sql_file(schema_sql)

    seed_auth_run()

    if vehicle_catalogs_seed_sql.exists():
        _execute_sql_file(vehicle_catalogs_seed_sql)
