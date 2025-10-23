from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from app.extensions import db

class BillingCustomer(db.Model):
    __tablename__ = "billing_customers"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey("orgs.id", ondelete="RESTRICT"), nullable=False, index=True)
    stripe_customer_id = db.Column(db.String(64), nullable=False, unique=True, index=True)

    billing_email = db.Column(db.String(255), nullable=True)
    default_payment_method = db.Column(db.String(64), nullable=True)

    billing_address_json = db.Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    tax_ids_json = db.Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    created_at = db.Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = db.Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    def __repr__(self) -> str:
        return f"<BillingCustomer id={self.id} org_id={self.org_id} stripe_customer_id={self.stripe_customer_id!r}>"
