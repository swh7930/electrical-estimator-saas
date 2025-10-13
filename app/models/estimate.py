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


class Material(db.Model):
    __tablename__ = "materials"
    __allow_unmapped__ = True
    
    id = db.Column(db.Integer, primary_key=True)

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
        # Partial-unique: prevent dup (type, description) among active rows
        Index(
            "ux_materials_type_desc_active_true",
            material_type,
            item_description,
            unique=True,
            postgresql_where=text("(is_active = true)"),
        ),
    )

    def __repr__(self) -> str:
        desc = (self.item_description or "").strip()
        return f"<Material id={self.id} type={self.material_type!r} desc={desc[:40]!r} active={self.is_active}>"


class DjeItem(db.Model):
    __tablename__ = "dje_items"
    __allow_unmapped__ = True
    
    id = db.Column(db.Integer, primary_key=True)

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
        Index(
            "ux_dje_items_cat_desc_vendor_active_true",
            category,
            description,
            vendor,
            unique=True,
            postgresql_where=text("(is_active = true)"),
        ),
    )

    def __repr__(self) -> str:
      vend = self.vendor or "-"
      desc = (self.description or "")[:40]
      return f"<DjeItem id={self.id} cat={self.category!r} desc={desc!r} vendor={vend!r} active={self.is_active}>"
