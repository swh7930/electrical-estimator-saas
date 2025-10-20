from sqlalchemy import func
from app.extensions import db

class Org(db.Model):
    __tablename__ = "orgs"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)  # simple label; can refine later
    is_active = db.Column(db.Boolean, nullable=False, server_default=db.text("true"))

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
