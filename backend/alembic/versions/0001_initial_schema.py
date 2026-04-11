"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-04-09 23:30:00

"""
from pathlib import Path

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def _schema_sql() -> str:
    here = Path(__file__).resolve()
    schema_path = here.parents[3] / "database" / "redline_schema.sql"
    return schema_path.read_text(encoding="utf-8")


def upgrade() -> None:
    op.execute(_schema_sql())


def downgrade() -> None:
    op.execute("""
    DROP SCHEMA IF EXISTS redline CASCADE;
    """)
