"""dje: per-org normalized unique index; retire global

Revision ID: ec330bbf71f5
Revises: 74ea543409d9
Create Date: 2025-10-29 10:46:09.855779

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ec330bbf71f5'
down_revision = '74ea543409d9'
branch_labels = None
depends_on = None


# Keep a tiny "system" index for org_id IS NULL (recommended = True)
ENABLE_SYSTEM_INDEX = True

def _detect_cols(bind):
    insp = sa.inspect(bind)
    cols = {c["name"].lower() for c in insp.get_columns("dje_items")}

    # type column: prefer 'category', fallback 'item_type'
    if "category" in cols:
        type_col = "category"
    elif "item_type" in cols:
        type_col = "item_type"
    else:
        raise RuntimeError("DJE: could not find a type column ('category' or 'item_type').")

    # description column: prefer 'description', fallback 'item_description'
    if "description" in cols:
        desc_col = "description"
    elif "item_description" in cols:
        desc_col = "item_description"
    else:
        raise RuntimeError("DJE: could not find a description column ('description' or 'item_description').")

    # vendor column optional
    vendor_col = "vendor" if "vendor" in cols else None

    # guard: must have org_id and is_active
    if "org_id" not in cols or "is_active" not in cols:
        raise RuntimeError("DJE: required columns missing ('org_id' and/or 'is_active').")

    return type_col, desc_col, vendor_col

def _norm_expr(col):
    # LOWER(TRIM(BOTH FROM col))
    return f"LOWER(TRIM(BOTH FROM {col}))"

def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    type_col, desc_col, vendor_col = _detect_cols(bind)
    type_norm = _norm_expr(type_col)
    desc_norm = _norm_expr(desc_col)
    if vendor_col:
        vendor_norm = f"COALESCE({_norm_expr(vendor_col)}, '')"
        key_list_per_org = f"org_id, {type_norm}, {desc_norm}, {vendor_norm}"
        key_list_system  = f"{type_norm}, {desc_norm}, {vendor_norm}"
    else:
        key_list_per_org = f"org_id, {type_norm}, {desc_norm}"
        key_list_system  = f"{type_norm}, {desc_norm}"

    # Pre-flight: block if within an org we already have normalized duplicates among ACTIVE rows.
    dupe_sql = sa.text(f"""
        WITH norm AS (
          SELECT
            org_id,
            {type_norm} AS t_norm,
            {desc_norm} AS d_norm
            {", " + vendor_norm + " AS v_norm" if vendor_col else ""}
          , COUNT(*) AS c,
            ARRAY_AGG(id ORDER BY id) AS ids
          FROM dje_items
          WHERE is_active = TRUE
          GROUP BY org_id, {type_norm}, {desc_norm}{", " + vendor_norm if vendor_col else ""}
        )
        SELECT org_id, t_norm, d_norm
               {", v_norm" if vendor_col else ""}
             , c, ids
        FROM norm
        WHERE c > 1
        ORDER BY org_id NULLS LAST, t_norm, d_norm{", v_norm" if vendor_col else ""};
    """)

    dupes = bind.execute(dupe_sql).fetchall()
    if dupes:
        preview = []
        for row in dupes[:10]:
            # row is a RowMapping; access by position for portability
            preview.append(str(dict(row._mapping)))
        raise RuntimeError(
            "Found per-org duplicate ACTIVE DJE items that would block the new per-org normalized index. "
            "Deactivate/resolve, then re-run migration.\n" + "\n".join(preview)
        )

    # Build DDL strings
    create_per_org = f"""
    CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS
      ux_dje_active_norm_per_org
    ON dje_items ( {key_list_per_org} )
    WHERE is_active = TRUE AND org_id IS NOT NULL;
    """

    create_system = f"""
    CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS
      ux_dje_active_norm_system
    ON dje_items ( {key_list_system} )
    WHERE is_active = TRUE AND org_id IS NULL;
    """

    # Legacy global normalized index name (ignore if not present)
    drop_legacy = "DROP INDEX IF EXISTS ux_dje_items_active_norm_key;"

    if dialect == "postgresql":
        with op.get_context().autocommit_block():
            op.execute(create_per_org)
            if ENABLE_SYSTEM_INDEX:
                op.execute(create_system)
            op.execute(drop_legacy)
    else:
        op.execute(create_per_org.replace(" CONCURRENTLY", ""))
        if ENABLE_SYSTEM_INDEX:
            op.execute(create_system.replace(" CONCURRENTLY", ""))
        op.execute(drop_legacy)

def downgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    # Recreate legacy global normalized unique index on ACTIVE rows (approximation; uses detected columns)
    type_col, desc_col, vendor_col = _detect_cols(bind)
    type_norm = _norm_expr(type_col)
    desc_norm = _norm_expr(desc_col)
    if vendor_col:
        vendor_norm = f"COALESCE({_norm_expr(vendor_col)}, '')"
        legacy_keys = f"{type_norm}, {desc_norm}, {vendor_norm}"
    else:
        legacy_keys = f"{type_norm}, {desc_norm}"

    recreate_legacy = f"""
    CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS
      ux_dje_items_active_norm_key
    ON dje_items ( {legacy_keys} )
    WHERE is_active = TRUE;
    """

    drop_per_org = "DROP INDEX IF EXISTS ux_dje_active_norm_per_org;"
    drop_system  = "DROP INDEX IF EXISTS ux_dje_active_norm_system;"

    if dialect == "postgresql":
        with op.get_context().autocommit_block():
            op.execute(drop_per_org)
            op.execute(drop_system)
            op.execute(recreate_legacy)
    else:
        op.execute(drop_per_org)
        op.execute(drop_system)
        op.execute(recreate_legacy.replace(" CONCURRENTLY", ""))