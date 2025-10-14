"""add legacy unique indexes required by importers

Revision ID: 1d07e8c26d7a
Revises: c530304dc93c
Create Date: 2025-10-13 13:46:25.264751

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1d07e8c26d7a'
down_revision = 'c530304dc93c'
branch_labels = None
depends_on = None


def upgrade():
    # Materials: legacy unique alias name expected by importer
    op.create_index(
        "ux_materials_active_norm_key",
        "materials",
        ["material_type", "item_description"],
        unique=True,
        postgresql_where=sa.text("(is_active = true)"),
    )

    # DJE: legacy unique alias name expected by importer
    op.create_index(
        "ux_dje_items_active_norm_key",
        "dje_items",
        ["category", "description", "vendor"],
        unique=True,
        postgresql_where=sa.text("(is_active = true)"),
    )
    
def downgrade():
    op.drop_index("ux_dje_items_active_norm_key", table_name="dje_items")
    op.drop_index("ux_materials_active_norm_key", table_name="materials")
