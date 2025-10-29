from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import Index, text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func

from app.extensions import db

"""
Estimator catalog models — critical indexes & constraints (doc only)

• materials
  - ix_materials_lower_item_description / ix_materials_lower_item_description_pattern:
    Functional BTREE indexes on lower(item_description) (pattern_ops) for fast ILIKE / prefix search.

  - ix_materials_material_type / ix_materials_type_active_desc:
    Common filtering/sorting paths for grid views (type + active + description).

  - ux_materials_type_desc_active_true:
    UNIQUE INDEX (material_type, item_description) WHERE is_active = true
    Rationale: Avoid duplicate live SKUs by type/description; allow inactive history.

  - chk_materials_unit (DB-level check):
    unit_quantity_size ∈ {1, 100, 1000} (enforced in DB, not re-declared in ORM to prevent autogen churn).

"""

class Material(db.Model):
    __tablename__ = "materials"
    __allow_unmapped__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    
    org_id = db.Column(db.Integer, db.ForeignKey("orgs.id", ondelete="CASCADE"), index=True, nullable=True)

    # Core attributes (nullable per baseline; DB is source of truth)
    material_type = db.Column(db.String, nullable=True)
    sku = db.Column(db.String, nullable=True)
    manufacturer = db.Column(db.String, nullable=True)
    item_description = db.Column(db.String, nullable=True)
    vendor = db.Column(db.String, nullable=True)

    # Pricing / labor
    price = db.Column(db.Numeric(10, 4), nullable=True)
    labor_unit = db.Column(db.Numeric(10, 4), nullable=True)

    # Unit rule (DB migration enforces CHECK + NOT NULL)
    unit_quantity_size = db.Column(db.Integer, nullable=False)

    # Cost-code enrichment (added in S3-03a.1)
    material_cost_code = db.Column(db.Text, nullable=True)
    mat_cost_code_desc = db.Column(db.Text, nullable=True)
    labor_cost_code = db.Column(db.Text, nullable=True)
    labor_cost_code_desc = db.Column(db.Text, nullable=True)

    # Lifecycle (added in S3-03a.4) — server-side defaults
    is_active = db.Column(db.Boolean, nullable=False, server_default=text("TRUE"))
    # Seed provenance (global + per‑org overlays)
    is_seed = db.Column(db.Boolean, nullable=False, server_default=text("FALSE"))
    seed_pack = db.Column(db.String, nullable=True)
    seed_version = db.Column(db.Integer, nullable=True)
    seed_key = db.Column(db.String, nullable=True)
    seeded_at = db.Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = db.Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at = db.Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )

    price: Optional[Decimal]
    labor_unit: Optional[Decimal]
    unit_quantity_size: int

    # Index strategy (doc):
    # - Case-insensitive search/prefix matches on description via functional indexes.
    # - Uniqueness within active catalog on (material_type, item_description).
    # - DB-level check enforces allowed unit_quantity_size values; we avoid duplicating that in ORM.
    __table_args__ = (
        # Case-insensitive search helpers on description
        Index("ix_materials_lower_item_description", func.lower(item_description)),
        Index(
            "ix_materials_lower_item_description_pattern", func.lower(item_description)
        ),
        # Common filters / sort
        Index("ix_materials_material_type", material_type),
        Index(
            "ix_materials_type_active_desc", material_type, is_active, item_description
        ),
        # Per‑org uniqueness for active materials (tenant‑scoped)
        Index(
            "ux_materials_org_type_desc_active_true",
            org_id,
            material_type,
            item_description,
            unique=True,
            postgresql_where=text("(is_active = true) AND (org_id IS NOT NULL)"),
        ),
        # Optional: preserve clean uniqueness for any future global rows
        Index(
            "ux_materials_type_desc_active_true_global",
            material_type,
            item_description,
            unique=True,
            postgresql_where=text("(is_active = true) AND (org_id IS NULL)"),
        ),
        # Seed idempotency — enforce uniqueness for global and per‑org seed rows
        Index(
            "ux_materials_seed_key_global_true",
            seed_key,
            unique=True,
            postgresql_where=text("(is_seed = true) AND (org_id IS NULL)"),
        ),
        Index(
            "ux_materials_org_seed_key_seeded_true",
            org_id,
            seed_key,
            unique=True,
            postgresql_where=text("(is_seed = true) AND (org_id IS NOT NULL)"),
        ),
    )

    def __repr__(self) -> str:
        desc = (self.item_description or "").strip()
        return f"<Material id={self.id} type={self.material_type!r} desc={desc[:40]!r} active={self.is_active}>"
