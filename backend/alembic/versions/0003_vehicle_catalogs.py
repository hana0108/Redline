"""add vehicle catalogs

Revision ID: 0003_vehicle_catalogs
Revises: 0002_client_images
Create Date: 2026-04-12 12:30:00

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0003_vehicle_catalogs"
down_revision = "0002_client_images"
branch_labels = None
depends_on = None


def _create_simple_catalog_table(table_name: str) -> None:
    op.create_table(
        table_name,
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.func.gen_random_uuid(),
            nullable=False,
            primary_key=True,
        ),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("code", name=f"uq_{table_name}_code"),
        schema="redline",
    )
    op.create_index(
        f"idx_{table_name}_active_sort", table_name, ["is_active", "sort_order"], schema="redline"
    )


def _create_trigger(table_name: str) -> None:
    op.execute(
        f"""
        DROP TRIGGER IF EXISTS trg_{table_name}_updated_at ON redline.{table_name};
        CREATE TRIGGER trg_{table_name}_updated_at
        BEFORE UPDATE ON redline.{table_name}
        FOR EACH ROW EXECUTE FUNCTION redline.set_updated_at();
        """
    )


def _drop_trigger(table_name: str) -> None:
    op.execute(f"DROP TRIGGER IF EXISTS trg_{table_name}_updated_at ON redline.{table_name};")


def upgrade() -> None:
    _create_simple_catalog_table("vehicle_brands")

    op.create_table(
        "vehicle_models_catalog",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.func.gen_random_uuid(),
            nullable=False,
            primary_key=True,
        ),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["brand_id"], ["redline.vehicle_brands.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("brand_id", "code", name="uq_vehicle_models_catalog_brand_code"),
        schema="redline",
    )
    op.create_index(
        "idx_vehicle_models_catalog_brand_active_sort",
        "vehicle_models_catalog",
        ["brand_id", "is_active", "sort_order"],
        schema="redline",
    )

    _create_simple_catalog_table("vehicle_types_catalog")
    _create_simple_catalog_table("fuel_types_catalog")
    _create_simple_catalog_table("transmissions_catalog")
    _create_simple_catalog_table("vehicle_colors_catalog")

    _create_trigger("vehicle_brands")
    _create_trigger("vehicle_models_catalog")
    _create_trigger("vehicle_types_catalog")
    _create_trigger("fuel_types_catalog")
    _create_trigger("transmissions_catalog")
    _create_trigger("vehicle_colors_catalog")


def downgrade() -> None:
    _drop_trigger("vehicle_colors_catalog")
    _drop_trigger("transmissions_catalog")
    _drop_trigger("fuel_types_catalog")
    _drop_trigger("vehicle_types_catalog")
    _drop_trigger("vehicle_models_catalog")
    _drop_trigger("vehicle_brands")

    op.drop_index(
        "idx_vehicle_colors_catalog_active_sort",
        table_name="vehicle_colors_catalog",
        schema="redline",
    )
    op.drop_table("vehicle_colors_catalog", schema="redline")

    op.drop_index(
        "idx_transmissions_catalog_active_sort",
        table_name="transmissions_catalog",
        schema="redline",
    )
    op.drop_table("transmissions_catalog", schema="redline")

    op.drop_index(
        "idx_fuel_types_catalog_active_sort", table_name="fuel_types_catalog", schema="redline"
    )
    op.drop_table("fuel_types_catalog", schema="redline")

    op.drop_index(
        "idx_vehicle_types_catalog_active_sort",
        table_name="vehicle_types_catalog",
        schema="redline",
    )
    op.drop_table("vehicle_types_catalog", schema="redline")

    op.drop_index(
        "idx_vehicle_models_catalog_brand_active_sort",
        table_name="vehicle_models_catalog",
        schema="redline",
    )
    op.drop_table("vehicle_models_catalog", schema="redline")

    op.drop_index("idx_vehicle_brands_active_sort", table_name="vehicle_brands", schema="redline")
    op.drop_table("vehicle_brands", schema="redline")
