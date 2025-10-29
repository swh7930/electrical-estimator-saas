"""materials: per-org normalized unique index; retire global

Revision ID: 74ea543409d9
Revises: 88363baf187c
Create Date: 2025-10-29 10:20:04.426733

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '74ea543409d9'
down_revision = '88363baf187c'
branch_labels = None
depends_on = None


# Toggle if you want the tiny global "system" index for org_id IS NULL.
ENABLE_SYSTEM_INDEX = True

_DUPES_QUERY = sa.text("""
WITH norm AS (
  SELECT
    org_id,
    LOWER(TRIM(BOTH FROM material_type)) AS mt_norm,
    LOWER(TRIM(BOTH FROM item_description)) AS desc_norm,
    COUNT(*) AS c,
    ARRAY_AGG(id ORDER BY id) AS ids
  FROM materials
  WHERE is_active = TRUE
  GROUP BY org_id,
    LOWER(TRIM(BOTH FROM material_type)),
    LOWER(TRIM(BOTH FROM item_description))
)
SELECT org_id, mt_norm, desc_norm, c, ids
FROM norm
WHERE c > 1
ORDER BY org_id NULLS LAST, mt_norm, desc_norm
""")

_CREATE_PER_ORG = """
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS
  ux_materials_active_norm_per_org
ON materials (
  org_id,
  LOWER(TRIM(BOTH FROM material_type)),
  LOWER(TRIM(BOTH FROM item_description))
)
WHERE is_active = TRUE AND org_id IS NOT NULL;
"""

_CREATE_SYSTEM = """
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS
  ux_materials_active_norm_system
ON materials (
  LOWER(TRIM(BOTH FROM material_type)),
  LOWER(TRIM(BOTH FROM item_description))
)
WHERE is_active = TRUE AND org_id IS NULL;
"""

_DROP_LEGACY = "DROP INDEX IF EXISTS ux_materials_active_norm_key;"

def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    # Pre-flight: block if there are per-org duplicates that would violate the new index.
    dupes = bind.execute(_DUPES_QUERY).fetchall()
    if dupes:
        # Show the first few to the deploy logs for quick triage.
        preview = []
        for row in dupes[:10]:
            preview.append(f"org_id={row.org_id} mt_norm='{row.mt_norm}' desc_norm='{row.desc_norm}' ids={list(row.ids)} count={row.c}")
        msg = (
            "Found per-org duplicate ACTIVE materials that would block "
            "ux_materials_active_norm_per_org. Deactivate/resolve these, then re-run migration.\n"
            + "\n".join(preview)
        )
        raise RuntimeError(msg)

    if dialect == "postgresql":
        # Run concurrent DDL outside of a transaction.
        with op.get_context().autocommit_block():
            op.execute(_CREATE_PER_ORG)
            if ENABLE_SYSTEM_INDEX:
                op.execute(_CREATE_SYSTEM)
            op.execute(_DROP_LEGACY)
    else:
        # Non-Postgres (e.g., SQLite in local dev tests) — create simple non-concurrent surrogates.
        op.execute(_CREATE_PER_ORG.replace(" CONCURRENTLY", ""))
        if ENABLE_SYSTEM_INDEX:
            op.execute(_CREATE_SYSTEM.replace(" CONCURRENTLY", ""))
        # Legacy name may not exist outside Postgres; safe to try.
        op.execute(_DROP_LEGACY)

def downgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    # Recreate the old global normalized unique index on ACTIVE rows (legacy behavior).
    recreate_legacy = """
    CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS
      ux_materials_active_norm_key
    ON materials (
      LOWER(TRIM(BOTH FROM material_type)),
      LOWER(TRIM(BOTH FROM item_description))
    )
    WHERE is_active = TRUE;
    """

    drop_per_org = "DROP INDEX IF EXISTS ux_materials_active_norm_per_org;"
    drop_system  = "DROP INDEX IF EXISTS ux_materials_active_norm_system;"

    if dialect == "postgresql":
        with op.get_context().autocommit_block():
            op.execute(drop_per_org)
            op.execute(drop_system)
            op.execute(recreate_legacy)
    else:
        op.execute(drop_per_org)
        op.execute(drop_system)
        op.execute(recreate_legacy.replace(" CONCURRENTLY", ""))