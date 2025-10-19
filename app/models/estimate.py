from __future__ import annotations

from sqlalchemy import Index, ForeignKey, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.sql import func

from app.extensions import db

class Estimate(db.Model):
    __tablename__ = "estimates"
    __allow_unmapped__ = True

    id = db.Column(db.Integer, primary_key=True)

    # Relations
    customer_id = db.Column(db.Integer, ForeignKey("customers.id"), nullable=True, index=True)

    # Basics
    name            = db.Column(db.String(255), nullable=False)
    project_address = db.Column(db.String(255), nullable=True)
    project_ref     = db.Column(db.String(255), nullable=True)
    status          = db.Column(db.String(32),  nullable=False, server_default=text("'draft'"))

    # Immutable snapshot of Admin → Settings at creation time
    settings_snapshot = db.Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    # Timestamps
    created_at = db.Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = db.Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (
        Index("ix_estimates_name", func.lower(name)),
        Index("ix_estimates_created_at", created_at),
    )

    def __repr__(self) -> str:
        return f"<Estimate id={self.id} name={self.name!r} status={self.status!r}>"

    def to_dict(self) -> dict:
        return dict(
            id=self.id,
            customer_id=self.customer_id,
            name=self.name,
            project_address=self.project_address,
            project_ref=self.project_ref,
            status=self.status,
            settings_snapshot=self.settings_snapshot,
            created_at=self.created_at.isoformat() if self.created_at else None,
            updated_at=self.updated_at.isoformat() if self.updated_at else None,
        )
