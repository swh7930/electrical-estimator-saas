from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Tuple

import pandas as pd
import sqlalchemy as sa
from sqlalchemy import text

from app.extensions import db


def _norm(val: object) -> str:
    """Lower/trim and collapse inner whitespace; None -> ''."""
    s = "" if val is None else str(val)
    s = re.sub(r"\s+", " ", s.strip().lower())
    return s


def _utcnow():
    return datetime.now(timezone.utc)


def import_materials_starter_pack(seed_pack: str = "starter", seed_version: int = 1) -> Tuple[int, int]:
    """
    Import/refresh the global Materials seed pack from data/Materials_DB_Seed.xlsx.
    Returns: (inserted_count, updated_count)
    """
    df = pd.read_excel("data/Materials_DB_Seed.xlsx")

    # Map workbook columns -> DB columns
    df = df.rename(
        columns={
            "Category": "material_type",
            "Item Description": "item_description",
            "Labor hrs": "labor_unit",
            "Cost": "price",
            "Unit": "unit_quantity_size",
            "SKU #": "sku",
            "Manufacturer": "manufacturer",
            "Vendor": "vendor",
            "Material Cost Code": "material_cost_code",
            "Mat Cost-Code Description": "mat_cost_code_desc",
            "Labor Cost Code": "labor_cost_code",
            "Labor Cost-Code Description": "labor_cost_code_desc",
        }
    )

    # Compute seed_key if not provided or missing
    if "seed_key" not in df.columns:
        df["seed_key"] = ""
    df["seed_key"] = df.apply(
        lambda r: r.get("seed_key") if isinstance(r.get("seed_key"), str) and r.get("seed_key").strip() else
        f"{_norm(r.get('material_type'))}|{_norm(r.get('item_description'))}|{_norm(r.get('manufacturer'))}|{_norm(r.get('sku'))}",
        axis=1,
    )

    # Defaults / coercions
    df["is_active"] = df.get("is_active", True).fillna(True).astype(bool)
    df["labor_unit"] = pd.to_numeric(df.get("labor_unit"), errors="coerce").fillna(0).round(2)
    df["price"] = pd.to_numeric(df.get("price"), errors="coerce").fillna(0).round(2)
    df["unit_quantity_size"] = pd.to_numeric(df.get("unit_quantity_size"), errors="coerce").fillna(1).astype(int)
    # Guard rails for unit_quantity_size
    invalid_units = ~df["unit_quantity_size"].isin([1, 100, 1000])
    if invalid_units.any():
        bad = df[invalid_units].iloc[0]
        raise ValueError(f"Invalid Unit Qty Size for seed_key={bad['seed_key']!r}; must be one of 1, 100, 1000.")

    # Preload existing global seed_keys to compute inserted vs updated
    existing = {
        row[0]
        for row in db.session.execute(
            text("SELECT seed_key FROM materials WHERE is_seed = true AND org_id IS NULL")
        ).all()
    }

    now = _utcnow()
    to_params = []
    inserted = 0
    updated = 0
    for _, r in df.iterrows():
        sk = r["seed_key"]
        if not sk:
            raise ValueError("Missing seed_key after normalization for a materials row.")

        # Count classification before upsert
        if sk in existing:
            updated += 1
        else:
            inserted += 1

        to_params.append(
            {
                "org_id": None,  # global seed
                "material_type": (r.get("material_type") or "").strip() or None,
                "item_description": (r.get("item_description") or "").strip() or None,
                "labor_unit": float(r.get("labor_unit") or 0),
                "price": float(r.get("price") or 0),
                "unit_quantity_size": int(r.get("unit_quantity_size") or 1),
                "sku": (r.get("sku") or None),
                "manufacturer": (r.get("manufacturer") or None),
                "vendor": (r.get("vendor") or None),
                "material_cost_code": (r.get("material_cost_code") or None),
                "mat_cost_code_desc": (r.get("mat_cost_code_desc") or None),
                "labor_cost_code": (r.get("labor_cost_code") or None),
                "labor_cost_code_desc": (r.get("labor_cost_code_desc") or None),
                "is_active": bool(r.get("is_active")),
                "seed_pack": seed_pack,
                "seed_version": int(seed_version),
                "seed_key": sk,
                "seeded_at": now,
            }
        )

    # Idempotent upsert using the unique seed_key index for global seeds
    # (relies on revision ce28d9cfd6bd which created the partial unique index).  :contentReference[oaicite:2]{index=2}
    sql = sa.text(
        """
        INSERT INTO materials (
            org_id, material_type, item_description, labor_unit, price, unit_quantity_size,
            sku, manufacturer, vendor,
            material_cost_code, mat_cost_code_desc, labor_cost_code, labor_cost_code_desc,
            is_active, is_seed, seed_pack, seed_version, seed_key, seeded_at, created_at, updated_at
        )
        VALUES (
            :org_id, :material_type, :item_description, :labor_unit, :price, :unit_quantity_size,
            :sku, :manufacturer, :vendor,
            :material_cost_code, :mat_cost_code_desc, :labor_cost_code, :labor_cost_code_desc,
            :is_active, true, :seed_pack, :seed_version, :seed_key, :seeded_at, now(), now()
        )
        ON CONFLICT (seed_key) DO UPDATE SET
            material_type        = EXCLUDED.material_type,
            item_description     = EXCLUDED.item_description,
            labor_unit           = EXCLUDED.labor_unit,
            price                = EXCLUDED.price,
            unit_quantity_size   = EXCLUDED.unit_quantity_size,
            sku                  = EXCLUDED.sku,
            manufacturer         = EXCLUDED.manufacturer,
            vendor               = EXCLUDED.vendor,
            material_cost_code   = EXCLUDED.material_cost_code,
            mat_cost_code_desc   = EXCLUDED.mat_cost_code_desc,
            labor_cost_code      = EXCLUDED.labor_cost_code,
            labor_cost_code_desc = EXCLUDED.labor_cost_code_desc,
            is_active            = EXCLUDED.is_active,
            seed_pack            = EXCLUDED.seed_pack,
            seed_version         = EXCLUDED.seed_version,
            seeded_at            = EXCLUDED.seeded_at,
            updated_at           = now()
        """
    )

    with db.session.begin():
        db.session.execute(sql, to_params)

    return inserted, updated


def import_dje_starter_pack(seed_pack: str = "starter", seed_version: int = 1) -> Tuple[int, int]:
    """
    Import/refresh the global DJE seed pack from data/dje_items.xlsx.
    Returns: (inserted_count, updated_count)
    """
    df = pd.read_excel("data/dje_items.xlsx")

    # Compute seed_key if not provided or missing
    if "seed_key" not in df.columns:
        df["seed_key"] = ""
    df["seed_key"] = df.apply(
        lambda r: r.get("seed_key") if isinstance(r.get("seed_key"), str) and r.get("seed_key").strip() else
        f"{_norm(r.get('category'))}|{_norm(r.get('description'))}|{_norm(r.get('vendor'))}",
        axis=1,
    )

    # Defaults / coercions
    df["is_active"] = df.get("is_active", True).fillna(True).astype(bool)
    df["default_unit_cost"] = pd.to_numeric(df.get("default_unit_cost"), errors="coerce").fillna(0).round(2)

    # Preload existing global seed_keys
    existing = {
        row[0]
        for row in db.session.execute(
            text("SELECT seed_key FROM dje_items WHERE is_seed = true AND org_id IS NULL")
        ).all()
    }

    now = _utcnow()
    to_params = []
    inserted = 0
    updated = 0
    for _, r in df.iterrows():
        sk = r["seed_key"]
        if not sk:
            raise ValueError("Missing seed_key after normalization for a DJE row.")

        if sk in existing:
            updated += 1
        else:
            inserted += 1

        to_params.append(
            {
                "org_id": None,
                "category": (r.get("category") or "").strip(),
                "subcategory": (r.get("subcategory") or None),
                "description": (r.get("description") or "").strip(),
                "default_unit_cost": float(r.get("default_unit_cost") or 0),
                "vendor": (r.get("vendor") or None),
                "cost_code": (r.get("cost_code") or None),
                "is_active": bool(r.get("is_active")),
                "seed_pack": seed_pack,
                "seed_version": int(seed_version),
                "seed_key": sk,
                "seeded_at": now,
            }
        )

    # Idempotent upsert using the unique seed_key index for global seeds
    # (relies on revision ce28d9cfd6bd).  :contentReference[oaicite:3]{index=3}
    sql = sa.text(
        """
        INSERT INTO dje_items (
            org_id, category, subcategory, description, default_unit_cost, vendor, cost_code,
            is_active, is_seed, seed_pack, seed_version, seed_key, seeded_at, created_at, updated_at
        )
        VALUES (
            :org_id, :category, :subcategory, :description, :default_unit_cost, :vendor, :cost_code,
            :is_active, true, :seed_pack, :seed_version, :seed_key, :seeded_at, now(), now()
        )
        ON CONFLICT (seed_key) DO UPDATE SET
            category          = EXCLUDED.category,
            subcategory       = EXCLUDED.subcategory,
            description       = EXCLUDED.description,
            default_unit_cost = EXCLUDED.default_unit_cost,
            vendor            = EXCLUDED.vendor,
            cost_code         = EXCLUDED.cost_code,
            is_active         = EXCLUDED.is_active,
            seed_pack         = EXCLUDED.seed_pack,
            seed_version      = EXCLUDED.seed_version,
            seeded_at         = EXCLUDED.seeded_at,
            updated_at        = now()
        """
    )

    with db.session.begin():
        db.session.execute(sql, to_params)

    return inserted, updated
