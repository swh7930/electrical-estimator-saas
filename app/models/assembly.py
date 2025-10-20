from __future__ import annotations

from typing import List

from sqlalchemy import Index, text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func

from app.extensions import db

"""
Assembly models — critical indexes & constraints (doc only)

• assemblies
  - uq_assemblies_lower_name_active_idx: UNIQUE INDEX on lower(name) WHERE is_active = true
    Rationale: Case-insensitive uniqueness for active assemblies; allows historical/inactive dupes.

  - ix_assemblies_category_active / ix_assemblies_subcategory_active / ix_assemblies_category_subcategory_active:
    FILTERED INDEXES (WHERE is_active = true) on lower(category/subcategory)
    Rationale: Fast admin browse/filter/suggest for the active catalog only.

• assembly_components
  - uq_ac_assembly_material_active_idx: UNIQUE INDEX on (assembly_id, material_id) WHERE is_active = true
    Rationale: Prevent duplicate materials on the same assembly while allowing soft-deleted history.

  - ix_ac_assembly / ix_ac_assembly_sort / ix_ac_material:
    Helper BTREE indexes for joins, sorted lists, and reverse lookups.

Notes:
- Partial-unique constraints are represented as UNIQUE INDEXes (SQLAlchemy cannot express partial UniqueConstraint).
- We intentionally define these in __table_args__ so Alembic autogenerate remains a no-op.
"""


class Assembly(db.Model):
    __tablename__ = "assemblies"
    __allow_unmapped__ = True
    
    org_id = db.Column(db.Integer, db.ForeignKey("orgs.id", ondelete="CASCADE"), index=True, nullable=True)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    assembly_code = db.Column(db.Text, nullable=True)  # reporting/future
    is_active = db.Column(db.Boolean, nullable=False, server_default=text("true"))
    created_at = db.Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at = db.Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )
    category = db.Column(db.Text, nullable=True)
    subcategory = db.Column(db.Text, nullable=True)
    is_featured = db.Column(db.Boolean, nullable=False, server_default=text("false"))

    # relationships
    components: List["AssemblyComponent"] = db.relationship(
        "AssemblyComponent",
        backref="assembly",
        lazy="select",
        passive_deletes=False,
        cascade="save-update, merge",
    )

    # Index strategy (doc):
    # - Unique among active rows: lower(name) enforces case-insensitive uniqueness while allowing inactive dupes.
    # - Filtered category/subcategory indexes accelerate admin filtering on active catalog only.
    __table_args__ = (
        # Partial unique: lower(name) must be unique among active rows
        Index(
            "uq_assemblies_lower_name_active_idx",
            func.lower(name),
            unique=True,
            postgresql_where=text("(is_active = true)"),
        ),
        # Filtered helpers for quick lookups in admin screens
        Index(
            "ix_assemblies_category_active",
            func.lower(category),
            postgresql_where=text("(is_active = true)"),
        ),
        Index(
            "ix_assemblies_subcategory_active",
            func.lower(subcategory),
            postgresql_where=text("(is_active = true)"),
        ),
        Index(
            "ix_assemblies_category_subcategory_active",
            func.lower(category),
            func.lower(subcategory),
            postgresql_where=text("(is_active = true)"),
        ),
    )
    
    def __repr__(self) -> str:
        return f"<Assembly id={self.id} name={self.name!r} active={self.is_active}>"


class AssemblyComponent(db.Model):
    __tablename__ = "assembly_components"

    id = db.Column(db.Integer, primary_key=True)
    assembly_id = db.Column(
        db.Integer, db.ForeignKey("assemblies.id", ondelete="RESTRICT"), nullable=False
    )
    material_id = db.Column(
        db.Integer, db.ForeignKey("materials.id", ondelete="RESTRICT"), nullable=False
    )
    qty_per_assembly = db.Column(db.Numeric(12, 4), nullable=False)
    sort_order = db.Column(db.Integer, nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, server_default=text("true"))
    created_at = db.Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at = db.Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )

    # Index strategy (doc):
    # - Helper indexes: (assembly_id), (assembly_id, sort_order), (material_id) for joins and stable ordering.
    # - Partial-unique on (assembly_id, material_id) WHERE is_active = true to prevent duplicate live links.
    __table_args__ = (
        # Standard helper indexes (match DB)
        Index("ix_ac_assembly", assembly_id),
        Index("ix_ac_assembly_sort", assembly_id, sort_order),
        Index("ix_ac_material", material_id),
        # Partial-unique to prevent dup materials on an assembly (while allowing inactive rows)
        Index(
            "uq_ac_assembly_material_active_idx",
            assembly_id,
            material_id,
            unique=True,
            postgresql_where=text("(is_active = true)"),
        ),
    )
    
    def __repr__(self) -> str:
        return (
            f"<AssemblyComponent id={self.id} asm_id={self.assembly_id} "
            f"material_id={self.material_id} qty={self.qty_per_assembly} active={self.is_active}>"
        )
