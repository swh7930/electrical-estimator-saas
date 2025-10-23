from sqlalchemy import func, text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from app.extensions import db

class Subscription(db.Model):
    __tablename__ = "subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey("orgs.id", ondelete="RESTRICT"), nullable=False, index=True)

    stripe_subscription_id = db.Column(db.String(64), nullable=False, unique=True, index=True)

    product_id = db.Column(db.String(64), nullable=False, index=True)
    price_id = db.Column(db.String(64), nullable=False, index=True)

    status = db.Column(db.String(32), nullable=False, index=True, server_default=text("'incomplete'"))
    cancel_at = db.Column(TIMESTAMP(timezone=True), nullable=True)
    cancel_at_period_end = db.Column(db.Boolean, nullable=False, server_default=text("false"))
    current_period_end = db.Column(TIMESTAMP(timezone=True), nullable=True, index=True)

    quantity = db.Column(db.Integer, nullable=False, server_default=text("1"))

    entitlements_json = db.Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))

    created_at = db.Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = db.Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (
        UniqueConstraint("org_id", name="uq_subscriptions_org_id"),
    )

    def __repr__(self) -> str:
        return f"<Subscription id={self.id} org_id={self.org_id} status={self.status!r} price_id={self.price_id!r}>"
