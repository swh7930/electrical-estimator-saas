from app.extensions import db


class DjeItem(db.Model):
    """
    Direct Job Expense (DJE) item.
    Used to populate DJE category, subcategory, and description dropdowns.
    """
    __tablename__ = "dje_items"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(120), index=True, nullable=False)
    subcategory = db.Column(db.String(120), index=True, nullable=True)
    description = db.Column(db.String(255), nullable=False)
    default_unit_cost = db.Column(db.Numeric(10, 2), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def to_dict(self):
        """Return minimal fields used by the frontend API."""
        return {
            "id": self.id,
            "category": self.category,
            "subcategory": self.subcategory,
            "description": self.description,
            "default_unit_cost": float(self.default_unit_cost or 0),
            "is_active": self.is_active,
        }
