"""S3-03b HK — overlay unique indexes (materials + dje)

Revision ID: c4a913ea3211
Revises: a4e5c7b90123
Create Date: 2025-10-24 08:42:37.689652

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4a913ea3211'
down_revision = 'a4e5c7b90123'
branch_labels = None
depends_on = None


def _drop_conflicting_unique_indexes(conn, table_name, patterns):
    """
    Drop any existing UNIQUE indexes on <table_name> whose indexdef contains *all* patterns.
    This is defensive so we don't depend on unknown historical names.
    """
    rows = conn.exec_driver_sql(
        "select indexname, indexdef "
        "from pg_indexes "
        "where schemaname = current_schema() and tablename = %s",
        (table_name,),
    ).all()
    for name, idxdef in rows:
        text = idxdef.lower()
        if " unique " not in text:
            continue
        if all(p.lower() in text for p in patterns):
            op.drop_index(name, table_name=table_name)


def upgrade():
    conn = op.get_bind()

    # ----- materials -----
    # Drop any old "active normalized key" unique that doesn't include org_id scoping
    _drop_conflicting_unique_indexes(
        conn,
        "materials",
        patterns=[
            "lower(trim(material_type))",
            "lower(trim(item_description))",
            "where",
            "is_active",
        ],
    )

    # Global (org_id IS NULL) unique on normalized key
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_materials_global_norm_key
        ON materials (
            (lower(trim(material_type))),
            (lower(trim(item_description)))
        )
        WHERE (is_active = true AND org_id IS NULL)
    """)

    # Org (org_id IS NOT NULL) unique on (org_id, normalized key)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_materials_org_norm_key
        ON materials (
            org_id,
            (lower(trim(material_type))),
            (lower(trim(item_description)))
        )
        WHERE (is_active = true AND org_id IS NOT NULL)
    """)

    # ----- dje_items -----
    _drop_conflicting_unique_indexes(
        conn,
        "dje_items",
        patterns=[
            "lower(trim(category))",
            "lower(trim(description))",
            "coalesce(lower(trim(vendor))",
            "where",
            "is_active",
        ],
    )

    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_dje_items_global_norm_key
        ON dje_items (
            (lower(trim(category))),
            (lower(trim(description))),
            (coalesce(lower(trim(vendor)), ''))
        )
        WHERE (is_active = true AND org_id IS NULL)
    """)

    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_dje_items_org_norm_key
        ON dje_items (
            org_id,
            (lower(trim(category))),
            (lower(trim(description))),
            (coalesce(lower(trim(vendor)), ''))
        )
        WHERE (is_active = true AND org_id IS NOT NULL)
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS ux_dje_items_org_norm_key")
    op.execute("DROP INDEX IF EXISTS ux_dje_items_global_norm_key")
    op.execute("DROP INDEX IF EXISTS ux_materials_org_norm_key")
    op.execute("DROP INDEX IF EXISTS ux_materials_global_norm_key")