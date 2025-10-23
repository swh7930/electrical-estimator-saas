from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from app.extensions import db

class BillingEventLog(db.Model):
    __tablename__ = "billing_event_logs"

    id = db.Column(db.Integer, primary_key=True)
    stripe_event_id = db.Column(db.String(255), nullable=False, unique=True, index=True)
    type = db.Column(db.String(80), nullable=False, index=True)
    signature_valid = db.Column(db.Boolean, nullable=False, server_default=text("true"))
    payload = db.Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    retries = db.Column(db.Integer, nullable=False, server_default=text("0"))
    notes = db.Column(db.String(255), nullable=True)

    processed_at = db.Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = db.Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
