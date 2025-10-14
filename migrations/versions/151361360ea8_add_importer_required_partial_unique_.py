"""Add importer-required partial unique indexes

Revision ID: 151361360ea8
Revises: 1d07e8c26d7a
Create Date: 2025-10-13 14:26:14.345299

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '151361360ea8'
down_revision = '1d07e8c26d7a'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_materials_active_norm_key
        ON materials (
            (lower(trim(material_type))),
            (lower(trim(item_description)))
        )
        WHERE (is_active = true);
    """)

    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_dje_items_active_norm_key
        ON dje_items (
            (lower(trim(category))),
            (lower(trim(description))),
            (coalesce(lower(trim(vendor)), ''))
        )
        WHERE (is_active = true);
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS ux_dje_items_active_norm_key;")
    op.execute("DROP INDEX IF EXISTS ux_materials_active_norm_key;")
