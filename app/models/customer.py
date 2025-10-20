from __future__ import annotations

from sqlalchemy import Index, text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func

from app.extensions import db


class Customer(db.Model):
    __tablename__ = "customers"
    __allow_unmapped__ = True

    id = db.Column(db.Integer, primary_key=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True)
    
    org_id = db.Column(db.Integer, db.ForeignKey("orgs.id", ondelete="CASCADE"), index=True, nullable=True)

    # Spec fields
    company_name = db.Column(db.String, nullable=True)
    contact_name = db.Column(db.String, nullable=True)
    email        = db.Column(db.String, nullable=True)
    phone        = db.Column(db.String, nullable=True)
    address1     = db.Column(db.String, nullable=True)
    address2     = db.Column(db.String, nullable=True)
    city         = db.Column(db.String, nullable=True)
    state        = db.Column(db.String(2), nullable=True)
    zip          = db.Column(db.String(10), nullable=True)

    notes = db.Column(db.Text, nullable=True)

    # Lifecycle
    is_active  = db.Column(db.Boolean, nullable=False, server_default=text("TRUE"))
    created_at = db.Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = db.Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (
        Index("ix_customers_company_name", company_name),
        Index("ix_customers_contact_name", contact_name),
        Index("ix_customers_city_active", city, is_active),  # kept from earlier; still useful
        Index("ix_customers_lower_email", func.lower(email)),
        Index("ix_customers_created_at", created_at),
    )

    def __repr__(self) -> str:
        return f"<Customer id={self.id} company={self.company_name!r} active={self.is_active}>"
