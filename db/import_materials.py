import pandas as pd
from sqlalchemy import create_engine, text
import os
from pathlib import Path
import numpy as np
from decimal import Decimal, InvalidOperation
from psycopg2.extras import execute_values
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.chdir(os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv; load_dotenv()

import logging

logger = logging.getLogger("importer.materials")


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        logger.error("env_missing key=DATABASE_URL")
        raise SystemExit(1)
    return url


# ---- Guardrail check --------------------------------------------------------
REQUIRED_INDEX = "ux_materials_active_norm_key"


def _assert_guardrail(conn):
    """Verify the required unique index exists before import."""
    exists = conn.execute(
        text(
            """
        SELECT 1
        FROM pg_indexes
        WHERE schemaname = 'public'
          AND tablename = 'materials'
          AND indexname = :idx
    """
        ),
        {"idx": REQUIRED_INDEX},
    ).fetchone()
    if not exists:
        raise SystemExit(
            f"ERROR: required unique index '{REQUIRED_INDEX}' not found.\n"
            "Run: flask --app app:create_app db upgrade first."
        )


# ---------------------------------------------------------------------------


def clean_str(value):
    if value is None:
        return ""
    s = str(value).strip()
    if s.lower() in ("nan", "none"):
        return ""
    return s


def to_decimal(value, default=Decimal("0")):
    s = clean_str(value)
    if s == "":
        return default
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return default


SEED_PATH = Path(os.getenv("MATERIALS_SEED_PATH", "data/Materials DB Seed.xlsx"))

# Load your Excel file
df = pd.read_excel(SEED_PATH)

# Rename columns to match DB schema
df = df.rename(
    columns={
        "Category": "material_type",
        "SKU #": "sku",
        "Manufacturer": "manufacturer",
        "Item Description": "item_description",
        "Vendor": "vendor",
        "Cost": "price",
        "Labor hrs": "labor_unit",
        "Unit": "unit_quantity_size",
        # New (optional) cost-code columns
        "Material Cost Code": "material_cost_code",
        "Mat Cost-Code Description": "mat_cost_code_desc",
        "Labor Cost Code": "labor_cost_code",
        "Labor Cost-Code Description": "labor_cost_code_desc",
    }
)

df = df[
    [
        "material_type",
        "sku",
        "manufacturer",
        "item_description",
        "vendor",
        "price",
        "labor_unit",
        "unit_quantity_size",
    ]
]

# Ensure optional cost-code cols exist (in case a sheet omits them)
for col in [
    "material_cost_code",
    "mat_cost_code_desc",
    "labor_cost_code",
    "labor_cost_code_desc",
]:
    if col not in df.columns:
        df[col] = None

# Keep only columns that exist in the DB now (including cost codes)
df = df[
    [
        "material_type",
        "sku",
        "manufacturer",
        "item_description",
        "vendor",
        "price",
        "labor_unit",
        "unit_quantity_size",
        "material_cost_code",
        "mat_cost_code_desc",
        "labor_cost_code",
        "labor_cost_code_desc",
    ]
]

# Enforce unit rule now, so later we can add a DB CHECK cleanly
VALID_UNITS = {1, 100, 1000}
bad = ~df["unit_quantity_size"].isin(VALID_UNITS)
if bad.any():
    raise ValueError(
        f"Unit must be 1, 100, or 1000. Found: {df.loc[bad, 'unit_quantity_size'].unique().tolist()}"
    )

# Normalize fields (strip text, coerce numerics, replace NaN with None)
for col in ["material_type", "sku", "manufacturer", "item_description", "vendor"]:
    df[col] = df[col].astype(str).str.strip()
df["price"] = pd.to_numeric(df["price"], errors="coerce").round(4).fillna(0)
df["labor_unit"] = pd.to_numeric(df["labor_unit"], errors="coerce").round(4).fillna(0)
df["unit_quantity_size"] = pd.to_numeric(
    df["unit_quantity_size"], errors="coerce"
).astype(int)
df = df.replace({np.nan: None})


# --- CLI wrapper (delegates to UPSERT) ---------------------------------------
def _run(
    dry_run: bool = False,
    limit: int | None = None,
    verbose: bool = False,
    fail_fast: bool = False,
) -> None:
    df_local = df.copy()
    if limit is not None:
        df_local = df_local.head(int(limit))
    _upsert_materials(df_local, dry_run=dry_run, verbose=verbose, fail_fast=fail_fast)


def _upsert_materials(
    df_local, *, dry_run: bool, verbose: bool, fail_fast: bool
) -> None:
    # Build rows with only the columns we actually write
    cols = [
        "material_type",
        "sku",
        "manufacturer",
        "item_description",
        "vendor",
        "price",
        "labor_unit",
        "unit_quantity_size",
        "material_cost_code",
        "mat_cost_code_desc",
        "labor_cost_code",
        "labor_cost_code_desc",
    ]
    dfw = df_local.reindex(columns=cols)

    # Basic observability
    logger.info("rows_prepared=%s", len(dfw))
    if verbose:
        logger.debug("preview:\n%s", dfw.head(min(5, len(dfw))).to_string(index=False))
        nn = {k: int(v) for k, v in dfw.notnull().sum().to_dict().items()}
        logger.debug("non_null=%s", nn)

    if dry_run:
        logger.info(
            logger.info("dry_run=true table=materials conflict=(lower(trim(material_type)),lower(trim(item_description))) predicate=is_active=true")
        )
        return

    engine = create_engine(get_database_url())
    with engine.begin() as conn:
        # Guardrail: require the Materials unique index before importing
        _exists = conn.execute(
            text(
                """
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'public'
                  AND tablename = 'materials'
                  AND indexname = 'ux_materials_active_norm_key'
            """
            )
        ).fetchone()
        if _exists is None:
            raise SystemExit(
                "ERROR: required unique index 'ux_materials_active_norm_key' missing. "
                "Run: flask --app app:create_app db upgrade"
            )
        before = conn.execute(
            text("SELECT COUNT(*) FROM materials WHERE is_active = true")
        ).scalar_one()
        # psycopg2 cursor for fast bulk upsert
        raw = conn.connection
        rows = [
            (
                r.material_type,
                r.sku,
                r.manufacturer,
                r.item_description,
                r.vendor,
                r.price,
                r.labor_unit,
                int(r.unit_quantity_size) if r.unit_quantity_size is not None else None,
                r.material_cost_code,
                r.mat_cost_code_desc,
                r.labor_cost_code,
                r.labor_cost_code_desc,
            )
            for r in dfw.itertuples(index=False, name="Row")
        ]
        if rows:
            sql = """
                INSERT INTO materials (
                    material_type, sku, manufacturer, item_description, vendor,
                    price, labor_unit, unit_quantity_size,
                    material_cost_code, mat_cost_code_desc, labor_cost_code, labor_cost_code_desc,
                    is_active
                ) VALUES %s
                ON CONFLICT (
                    (lower(trim(material_type))),
                    (lower(trim(item_description)))
                )
                WHERE (is_active = true)
                DO UPDATE SET
                    sku = EXCLUDED.sku,
                    manufacturer = EXCLUDED.manufacturer,
                    vendor = EXCLUDED.vendor,
                    price = EXCLUDED.price,
                    labor_unit = EXCLUDED.labor_unit,
                    unit_quantity_size = EXCLUDED.unit_quantity_size,
                    material_cost_code = EXCLUDED.material_cost_code,
                    mat_cost_code_desc = EXCLUDED.mat_cost_code_desc,
                    labor_cost_code = EXCLUDED.labor_cost_code,
                    labor_cost_code_desc = EXCLUDED.labor_cost_code_desc,
                    updated_at = NOW()
            """
            with raw.cursor() as cur:
                # Append constant is_active=True as a separate column value
                rows_with_active = [tuple(list(t) + [True]) for t in rows]
                try:
                    execute_values(cur, sql, rows_with_active, page_size=1000)
                except Exception as e:
                    if fail_fast:
                        raise
                    logger.error("upsert_failed error=%s", e)
                    raise SystemExit(2)
        after = conn.execute(
            text("SELECT COUNT(*) FROM materials WHERE is_active = true")
        ).scalar_one()
        inserted = max(0, (after - before))
        logger.info(
            "upsert_complete table=materials before=%s after=%s inserted_est=%s",
            before,
            after,
            inserted,
        )


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(
        description="Import materials into DB safely (idempotent UPSERT)."
    )
    p.add_argument(
        "--dry-run", action="store_true", help="Plan only; print what would happen."
    )
    p.add_argument(
        "--limit", type=int, default=None, help="Limit number of rows to process."
    )
    p.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output (preview & stats)."
    )
    p.add_argument(
        "--fail-fast", action="store_true", help="Raise immediately on the first error."
    )
    args = p.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    _run(
        dry_run=args.dry_run,
        limit=args.limit,
        verbose=args.verbose,
        fail_fast=args.fail_fast,
    )
    raise SystemExit(0)
