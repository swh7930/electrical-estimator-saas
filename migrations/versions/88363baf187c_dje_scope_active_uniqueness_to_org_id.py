"""dje: scope active uniqueness to org_id

Revision ID: 88363baf187c
Revises: 132ea766ab99
Create Date: 2025-10-29 09:03:07.287450

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '88363baf187c'
down_revision = '132ea766ab99'
branch_labels = None
depends_on = None


def upgrade():
    # Drop legacy GLOBAL active unique; create tenant-scoped + global-only active uniques.
    with op.batch_alter_table('dje_items', schema=None) as batch_op:
        # 1) Remove the old global unique that caused cross-tenant collisions
        batch_op.drop_index('ux_dje_items_cat_desc_vendor_active_true')

        # 2) Per-org active uniqueness (tenant-scoped)
        batch_op.create_index(
            'ux_dje_items_org_cat_desc_vendor_active_true',
            ['org_id', 'category', 'description', 'vendor'],
            unique=True,
            postgresql_where=sa.text('(is_active = true) AND (org_id IS NOT NULL)')
        )

        # 3) Global-only active uniqueness (for any future system rows)
        batch_op.create_index(
            'ux_dje_items_cat_desc_vendor_active_true_global',
            ['category', 'description', 'vendor'],
            unique=True,
            postgresql_where=sa.text('(is_active = true) AND (org_id IS NULL)')
        )


def downgrade():
    # Recreate the legacy GLOBAL active unique and remove the tenant-scoped/global-only pair.
    with op.batch_alter_table('dje_items', schema=None) as batch_op:
        batch_op.drop_index('ux_dje_items_cat_desc_vendor_active_true_global')
        batch_op.drop_index('ux_dje_items_org_cat_desc_vendor_active_true')

        batch_op.create_index(
            'ux_dje_items_cat_desc_vendor_active_true',
            ['category', 'description', 'vendor'],
            unique=True,
            postgresql_where=sa.text('(is_active = true)')
        )