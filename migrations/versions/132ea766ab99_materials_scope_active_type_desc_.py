"""materials: scope active type/desc uniqueness to org_id

Revision ID: 132ea766ab99
Revises: ce28d9cfd6bd
Create Date: 2025-10-29 08:10:54.353644

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '132ea766ab99'
down_revision = 'ce28d9cfd6bd'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the legacy GLOBAL unique index that enforces cross-tenant uniqueness
    with op.batch_alter_table('materials', schema=None) as batch_op:
        batch_op.drop_index('ux_materials_type_desc_active_true')

        # Create tenant-scoped unique index for ACTIVE rows per org
        batch_op.create_index(
            'ux_materials_org_type_desc_active_true',
            ['org_id', 'material_type', 'item_description'],
            unique=True,
            postgresql_where=sa.text('(is_active = true) AND (org_id IS NOT NULL)')
        )

        # Optional: keep a clean GLOBAL unique index for ACTIVE rows (org_id IS NULL)
        batch_op.create_index(
            'ux_materials_type_desc_active_true_global',
            ['material_type', 'item_description'],
            unique=True,
            postgresql_where=sa.text('(is_active = true) AND (org_id IS NULL)')
        )


def downgrade():
    with op.batch_alter_table('materials', schema=None) as batch_op:
        # Drop the tenant-scoped and global-scope replacements
        batch_op.drop_index('ux_materials_type_desc_active_true_global')
        batch_op.drop_index('ux_materials_org_type_desc_active_true')

        # Recreate the original GLOBAL unique index for ACTIVE rows (pre-change behavior)
        batch_op.create_index(
            'ux_materials_type_desc_active_true',
            ['material_type', 'item_description'],
            unique=True,
            postgresql_where=sa.text('(is_active = true)')
        )