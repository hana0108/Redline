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
    # Create client_images table
    op.create_table(
        'client_images',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.func.gen_random_uuid(), nullable=False, primary_key=True),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_cover', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['client_id'], ['redline.clients.id'], ondelete='CASCADE'),
        schema='redline'
    )

    # Create index
    op.create_index('idx_client_images_client', 'client_images', ['client_id'], schema='redline')

    # Create trigger
    op.execute("""
    DROP TRIGGER IF EXISTS trg_client_images_updated_at ON redline.client_images;
    CREATE TRIGGER trg_client_images_updated_at BEFORE UPDATE ON redline.client_images FOR EACH ROW EXECUTE FUNCTION redline.set_updated_at();
    """)


def downgrade() -> None:
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS trg_client_images_updated_at ON redline.client_images;")

    # Drop index
    op.drop_index('idx_client_images_client', table_name='client_images', schema='redline')

    # Drop table
    op.drop_table('client_images', schema='redline')
