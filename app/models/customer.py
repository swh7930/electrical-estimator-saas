from __future__ import annotations

from sqlalchemy import Index, text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func

from app.extensions import db


class Customer(db.Model):
    __tablename__ = "customers"
    __allow_unmapped__ = True

    id = db.Column(db.Integer, primary_key=True)

    # Core
    name = db.Column(db.String, nullable=False)
    primary_contact = db.Column(db.String, nullable=True)
    email = db.Column(db.String, nullable=True)
    phone = db.Column(db.String, nullable=True)
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # Lifecycle
    is_active = db.Column(db.Boolean, nullable=False, server_default=text("TRUE"))
    created_at = db.Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = db.Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (
        # Search/sort helpers
        Index("ix_customers_lower_name", func.lower(name)),
        Index("ix_customers_city_active", city, is_active),
        # Prevent duplicate *active* names while allowing historical dupes
        Index(
            "ux_customers_lower_name_active_true",
            func.lower(name),
            unique=True,
            postgresql_where=text("(is_active = true)"),
        ),
    )

    def __repr__(self) -> str:
        return f"<Customer id={self.id} name={self.name!r} active={self.is_active}>"
