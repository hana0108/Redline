"""Add client_images table

Revision ID: 0002_client_images
Revises: 0001_initial_schema
Create Date: 2026-04-12 10:00:00

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_client_images"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # client_images is already included in redline_schema.sql (initial migration).
    # This migration is kept for history tracking only.
    op.execute("""
    CREATE TABLE IF NOT EXISTS redline.client_images (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        client_id uuid NOT NULL REFERENCES redline.clients(id) ON DELETE CASCADE,
        file_path text NOT NULL,
        sort_order integer NOT NULL DEFAULT 0,
        is_cover boolean NOT NULL DEFAULT false,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_client_images_client ON redline.client_images(client_id);
    DROP TRIGGER IF EXISTS trg_client_images_updated_at ON redline.client_images;
    CREATE TRIGGER trg_client_images_updated_at BEFORE UPDATE ON redline.client_images FOR EACH ROW EXECUTE FUNCTION redline.set_updated_at();
    """)


def downgrade() -> None:
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS trg_client_images_updated_at ON redline.client_images;")

    # Drop index
    op.drop_index("idx_client_images_client", table_name="client_images", schema="redline")

    # Drop table
    op.drop_table("client_images", schema="redline")
