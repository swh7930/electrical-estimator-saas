import os
from pathlib import Path
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from psycopg2.extras import execute_values
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.chdir(os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv; load_dotenv()

import logging

logger = logging.getLogger("importer.dje")


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        print(
            "ERROR: DATABASE_URL not set. Please export or add to .env.",
            file=sys.stderr,
        )
        sys.exit(1)
    return url


REQUIRED_INDEX = "ux_dje_items_active_norm_key"


def _assert_guardrail(conn):
    exists = conn.execute(
        text(
            """
        SELECT 1
        FROM pg_indexes
        WHERE schemaname = 'public'
          AND tablename = 'dje_items'
          AND indexname = :idx
    """
        ),
        {"idx": REQUIRED_INDEX},
    ).fetchone()
    if not exists:
        raise SystemExit(
            f"ERROR: required unique index '{REQUIRED_INDEX}' not found. "
            "Run: flask --app app:create_app db upgrade"
        )


# === Config (env-overridable) ===============================================
SEED_PATH = Path(os.getenv("DJE_SEED_PATH", "data/dje_items.xlsx"))
SHEET_NAME = os.getenv("DJE_SHEET_NAME")  # optional

# === Load Excel ==============================================================
if SHEET_NAME:
    df = pd.read_excel(SEED_PATH, sheet_name=SHEET_NAME)
else:
    df = pd.read_excel(SEED_PATH)

# Normalize headers (trim/case)
df.columns = [str(c).strip() for c in df.columns]

# Drop non-DB columns present in seed
for drop_col in ["id", "ID", "Unit", "unit"]:
    if drop_col in df.columns:
        df = df.drop(columns=[drop_col])

# Rename to DB column names if needed
rename_map = {
    "Category": "category",
    "Subcategory": "subcategory",
    "Description": "description",
    "Vendor": "vendor",
    "Default Unit Cost": "default_unit_cost",
    "Cost Code": "cost_code",
}
df = df.rename(columns=rename_map)

# Ensure expected columns exist; create blanks if missing
for col in [
    "category",
    "subcategory",
    "description",
    "vendor",
    "default_unit_cost",
    "cost_code",
    "is_active",
]:
    if col not in df.columns:
        df[col] = None

# Keep only table columns (order matters for to_sql)
df = df[
    [
        "category",
        "subcategory",
        "description",
        "vendor",
        "default_unit_cost",
        "cost_code",
        "is_active",
    ]
].copy()

# Text cleanup
for col in ["category", "subcategory", "description", "vendor", "cost_code"]:
    df[col] = df[col].astype(str).str.strip()
    df.loc[df[col].isin(["", "nan", "None", "NaN"]), col] = None

# Cost → numeric(12,4)-style
df["default_unit_cost"] = (
    pd.to_numeric(df["default_unit_cost"], errors="coerce").round(4).fillna(0)
)


# is_active default TRUE if blank
def to_bool(x):
    if x is None or (isinstance(x, float) and np.isnan(x)) or str(x).strip() == "":
        return True
    s = str(x).strip().lower()
    return s in ("true", "t", "yes", "y", "1")


df["is_active"] = df["is_active"].map(to_bool)

# Replace NaN with None for SQL NULLs
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
    _upsert_dje(df_local, dry_run=dry_run, verbose=verbose, fail_fast=fail_fast)


def _upsert_dje(df_local, *, dry_run: bool, verbose: bool, fail_fast: bool) -> None:
    cols = [
        "category",
        "subcategory",
        "description",
        "vendor",
        "default_unit_cost",
        "cost_code",
    ]
    dfw = df_local.reindex(columns=cols)

    logger.info("rows_prepared=%s source=%s", len(dfw), SEED_PATH)
    if verbose:
        logger.debug("preview:\n%s", dfw.head(min(5, len(dfw))).to_string(index=False))
        nn = {k: int(v) for k, v in dfw.notnull().sum().to_dict().items()}
        logger.debug("non_null=%s", nn)

    if dry_run:
        logger.info(
            logger.info("dry_run=true table=dje_items conflict=(lower(trim(category)),lower(trim(description)),coalesce(lower(trim(vendor)),'')) predicate=is_active=true")
        )
        return

    engine = create_engine(get_database_url())
    with engine.begin() as conn:
        # Guardrail: require the DJE unique index before importing
        _assert_guardrail(conn)
        before = conn.execute(
            text("SELECT COUNT(*) FROM dje_items WHERE is_active = true")
        ).scalar_one()
        raw = conn.connection
        rows = [
            (
                r.category,
                r.subcategory,
                r.description,
                r.vendor,
                r.default_unit_cost,
                r.cost_code,
            )
            for r in dfw.itertuples(index=False, name="Row")
        ]
        if rows:
            sql = """
                INSERT INTO dje_items (
                    category, subcategory, description, vendor,
                    default_unit_cost, cost_code, is_active
                ) VALUES %s
                ON CONFLICT (
                    (lower(trim(category))),
                    (lower(trim(description))),
                    (coalesce(lower(trim(vendor)), ''))
                    )
                    WHERE (is_active = true)
                    DO UPDATE SET
                    subcategory = EXCLUDED.subcategory,
                    default_unit_cost = EXCLUDED.default_unit_cost,
                    cost_code = EXCLUDED.cost_code,
                    updated_at = NOW()
            """
            with raw.cursor() as cur:
                rows_with_active = [tuple(list(t) + [True]) for t in rows]
                try:
                    execute_values(cur, sql, rows_with_active, page_size=1000)
                except Exception as e:
                    if fail_fast:
                        raise
                    logger.error("upsert_failed error=%s", e)
                    raise SystemExit(2)
        after = conn.execute(
            text("SELECT COUNT(*) FROM dje_items WHERE is_active = true")
        ).scalar_one()
        inserted = max(0, (after - before))
        logger.info(
            "upsert_complete table=dje_items before=%s after=%s inserted_est=%s",
            before,
            after,
            inserted,
        )


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(
        description="Import DJE items into DB safely (idempotent UPSERT)."
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
# ---------------------------------------------------------------------------
