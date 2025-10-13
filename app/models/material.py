from app.extensions import db


class Material(db.Model):
    __tablename__ = "materials"

    id = db.Column(db.Integer, primary_key=True)
    material_type = db.Column(db.String(120), index=True, nullable=False)
    sku = db.Column(db.String(120))
    manufacturer = db.Column(db.String(120))
    item_description = db.Column(db.String(255), nullable=False)
    vendor = db.Column(db.String(120))
    price = db.Column(db.Numeric(10, 2))
    labor_unit = db.Column(db.Numeric(10, 4))
    unit_quantity_size = db.Column(db.String(64))
    material_cost_code = db.Column(db.String(64))
    mat_cost_code_desc = db.Column(db.String(255))
    labor_cost_code = db.Column(db.String(64))
    labor_cost_code_desc = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def to_dict(self):
        """Serialize minimal fields for JSON responses."""
        return {
            "id": self.id,
            "material_type": self.material_type,
            "sku": self.sku,
            "manufacturer": self.manufacturer,
            "item_description": self.item_description,
            "vendor": self.vendor,
            "price": float(self.price or 0),
            "labor_unit": float(self.labor_unit or 0),
            "unit_quantity_size": self.unit_quantity_size,
            "material_cost_code": self.material_cost_code,
            "mat_cost_code_desc": self.mat_cost_code_desc,
            "labor_cost_code": self.labor_cost_code,
            "labor_cost_code_desc": self.labor_cost_code_desc,
            "is_active": self.is_active,
        }
