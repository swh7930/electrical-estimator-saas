from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import Index, text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func

from app.extensions import db

"""
Estimator catalog models — critical indexes & constraints (doc only)
• dje_items
  - ix_dje_items_category / ix_dje_items_cat_sub_desc:
    Category/Subcategory browse and search helpers.

  - ix_dje_items_lower_description / ix_dje_items_lower_description_pattern:
    Case-insensitive search and prefix matching on description.

  - ux_dje_items_cat_desc_vendor_active_true:
    UNIQUE INDEX (category, description, vendor) WHERE is_active = true
    Rationale: Catalog-level de-dup of active items per vendor.

  - chk_dje_items_unit_cost_nonneg (DB-level check):
    default_unit_cost ≥ 0 (enforced in DB).
"""


class DjeItem(db.Model):
    __tablename__ = "dje_items"
    __allow_unmapped__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    
    org_id = db.Column(db.Integer, db.ForeignKey("orgs.id", ondelete="CASCADE"), index=True, nullable=True)

    # Classification
    category = db.Column(db.String, nullable=False)
    subcategory = db.Column(db.String, nullable=True)

    # Display / selection
    description = db.Column(db.String, nullable=False)
    vendor = db.Column(db.String, nullable=True)

    # Default pricing (non-negative; DB has server_default and CHECK)
    default_unit_cost = db.Column(
        db.Numeric(12, 4), nullable=False, server_default=text("0")
    )

    # Optional cost code (added in S3-03b.1a)
    cost_code = db.Column(db.Text, nullable=True)

    # Lifecycle — server-side defaults
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

    default_unit_cost: Decimal
    vendor: Optional[str]

    # Index strategy (doc):
    # - Category/subcategory search helpers + case-insensitive description search.
    # - Active-catalog uniqueness on (category, description, vendor).
    # - DB-level check ensures non-negative default_unit_cost.
    __table_args__ = (
        Index("ix_dje_items_category", category),
        Index("ix_dje_items_cat_sub_desc", category, subcategory, description),
        Index("ix_dje_items_lower_description", func.lower(description)),
        Index("ix_dje_items_lower_description_pattern", func.lower(description)),
        # Partial-unique across active catalog
        # Per‑org uniqueness for active DJE items (tenant‑scoped)
        Index(
            "ux_dje_items_org_cat_desc_vendor_active_true",
            org_id,
            category,
            description,
            vendor,
            unique=True,
            postgresql_where=text("(is_active = true) AND (org_id IS NOT NULL)"),
        ),
        # Optional: keep clean uniqueness for any future global rows
        Index(
            "ux_dje_items_cat_desc_vendor_active_true_global",
            category,
            description,
            vendor,
            unique=True,
            postgresql_where=text("(is_active = true) AND (org_id IS NULL)"),
        ),
        # Seed idempotency — enforce uniqueness for global and per‑org seed rows
        Index(
            "ux_dje_items_seed_key_global_true",
            seed_key,
            unique=True,
            postgresql_where=text("(is_seed = true) AND (org_id IS NULL)"),
        ),
        Index(
            "ux_dje_items_org_seed_key_seeded_true",
            org_id,
            seed_key,
            unique=True,
            postgresql_where=text("(is_seed = true) AND (org_id IS NOT NULL)"),
        ),
    )

    def __repr__(self) -> str:
      vend = self.vendor or "-"
      desc = (self.description or "")[:40]
      return f"<DjeItem id={self.id} cat={self.category!r} desc={desc!r} vendor={vend!r} active={self.is_active}>"
