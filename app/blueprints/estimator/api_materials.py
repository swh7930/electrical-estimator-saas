from flask import jsonify, request, current_app
from . import bp
from flask_login import current_user
from app.extensions import db
from app.models.material import Material
from sqlalchemy import func, or_, and_, exists
from sqlalchemy.orm import aliased


@bp.get("/api/material-types")
def get_material_types():
    """Return distinct active material types."""
    try:
        rows = (
        db.session.query(Material.material_type)
        .filter(Material.is_active.is_(True))
        .filter(or_(Material.org_id == current_user.org_id, Material.org_id.is_(None)))
        .distinct()
        .order_by(Material.material_type)
        .all()
    )
        return jsonify([r[0] for r in rows if r[0]]), 200
    except Exception as e:
        current_app.logger.exception("GET /api/material-types failed")
        return jsonify({"error": "server_error", "detail": str(e)}), 500

@bp.get("/api/material-descriptions")
def get_material_descriptions():
    """Return item details for a given material type (org overrides > global)."""
    try:
        mat_type = (request.args.get("type") or "").strip()
        if not mat_type:
            return jsonify([]), 200

        O = aliased(Material)
        rows = (
            db.session.query(
                Material.id,
                Material.item_description,
                Material.price,
                Material.labor_unit,
                Material.unit_quantity_size,
            )
            .filter(Material.is_active.is_(True))
            .filter(Material.material_type == mat_type)
            .filter(
                or_(
                    Material.org_id == current_user.org_id,                        # org row (override or org-only)
                    and_(
                        Material.org_id.is_(None),                                 # global row
                        ~exists().where(and_(                                      # not overridden by this org
                            O.is_active.is_(True),
                            O.org_id == current_user.org_id,
                            func.lower(func.trim(O.material_type)) == func.lower(func.trim(Material.material_type)),
                            func.lower(func.trim(O.item_description)) == func.lower(func.trim(Material.item_description)),
                        ))
                    ),
                )
            )
            .order_by(func.lower(Material.item_description).asc())
            .all()
        )

        def per_each(price, labor, unit):
            try:
                u = int(unit or 1)
                if u <= 0:
                    u = 1
            except Exception:
                u = 1
            pe = float(price or 0) / u
            le = float(labor or 0) / u
            return pe, le

        result = []
        for mid, desc, price, labor, unit in rows:
            price_each, labor_each = per_each(price, labor, unit)
            result.append(
                {
                    "id": mid,
                    "item_description": desc,
                    "price": float(price or 0),
                    "labor_unit": float(labor or 0),
                    "unit_quantity_size": unit or 1,
                    "price_each": round(price_each, 4),
                    "labor_each": round(labor_each, 4),
                }
            )

        return jsonify(result), 200

    except Exception as e:
        current_app.logger.exception("GET /api/material-descriptions failed")
        return jsonify({"error": "server_error", "detail": str(e)}), 500
