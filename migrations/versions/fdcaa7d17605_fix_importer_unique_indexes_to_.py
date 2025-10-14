"""Fix importer unique indexes to expression-based partials

Revision ID: fdcaa7d17605
Revises: 151361360ea8
Create Date: 2025-10-13 15:19:45.609777

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fdcaa7d17605'
down_revision = '151361360ea8'
branch_labels = None
depends_on = None


def upgrade():
    # Recreate MATERIALS index with exact expression + predicate
    op.execute("DROP INDEX IF EXISTS ux_materials_active_norm_key;")
    op.execute("""
        CREATE UNIQUE INDEX ux_materials_active_norm_key
        ON public.materials (
            (lower(trim(material_type))),
            (lower(trim(item_description)))
        )
        WHERE (is_active = true);
    """)

    # Recreate DJE index with exact expression + predicate
    op.execute("DROP INDEX IF EXISTS ux_dje_items_active_norm_key;")
    op.execute("""
        CREATE UNIQUE INDEX ux_dje_items_active_norm_key
        ON public.dje_items (
            (lower(trim(category))),
            (lower(trim(description))),
            (coalesce(lower(trim(vendor)), ''))
        )
        WHERE (is_active = true);
    """)


def downgrade():
    # Roll back to the plain-column versions (optional)
    op.execute("DROP INDEX IF EXISTS ux_dje_items_active_norm_key;")
    op.execute("DROP INDEX IF EXISTS ux_materials_active_norm_key;")

    op.execute("""
        CREATE UNIQUE INDEX ux_materials_active_norm_key
        ON public.materials (material_type, item_description)
        WHERE (is_active = true);
    """)
    op.execute("""
        CREATE UNIQUE INDEX ux_dje_items_active_norm_key
        ON public.dje_items (category, description, vendor)
        WHERE (is_active = true);
    """)
