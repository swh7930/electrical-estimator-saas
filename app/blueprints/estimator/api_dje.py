from flask import jsonify, request, current_app
from . import bp
from app.extensions import db
from app.models.dje_item import DjeItem


@bp.get("/api/dje-categories")
def get_dje_categories():
    """Return distinct DJE categories."""
    try:
        rows = (
            db.session.query(DjeItem.category)
            .filter(DjeItem.is_active.is_(True))
            .filter(DjeItem.category.isnot(None))
            .filter(DjeItem.category != "")
            .distinct()
            .order_by(DjeItem.category.asc())
            .all()
        )
        return jsonify([r[0] for r in rows]), 200
    except Exception as e:
        current_app.logger.exception("GET /api/dje-categories failed")
        return jsonify({"error": "server_error", "detail": str(e)}), 500


@bp.get("/api/dje-subcategories")
def get_dje_subcategories():
    """Return subcategories for a given DJE category."""
    try:
        category = (request.args.get("category") or "").strip()
        if not category:
            return jsonify([]), 200

        rows = (
            db.session.query(DjeItem.subcategory)
            .filter(DjeItem.is_active.is_(True))
            .filter(DjeItem.category == category)
            .filter(DjeItem.subcategory.isnot(None))
            .filter(DjeItem.subcategory != "")
            .distinct()
            .order_by(DjeItem.subcategory.asc())
            .all()
        )
        return jsonify([r[0] for r in rows]), 200
    except Exception as e:
        current_app.logger.exception("GET /api/dje-subcategories failed")
        return jsonify({"error": "server_error", "detail": str(e)}), 500


@bp.get("/api/dje-descriptions")
def get_dje_descriptions():
    """Return DJE items for a category/subcategory pair."""
    try:
        category = (request.args.get("category") or "").strip()
        subcat = (request.args.get("subcategory") or "").strip()
        if not category or not subcat:
            return jsonify([]), 200

        rows = (
            db.session.query(
                DjeItem.id,
                DjeItem.description,
                DjeItem.default_unit_cost,
            )
            .filter(DjeItem.is_active.is_(True))
            .filter(DjeItem.category == category)
            .filter(DjeItem.subcategory == subcat)
            .filter(DjeItem.description.isnot(None))
            .filter(DjeItem.description != "")
            .order_by(DjeItem.description.asc())
            .all()
        )
        return (
            jsonify(
                [
                    {"id": rid, "description": desc, "cost": float(cost or 0)}
                    for (rid, desc, cost) in rows
                ]
            ),
            200,
        )
    except Exception as e:
        current_app.logger.exception("GET /api/dje-descriptions failed")
        return jsonify({"error": "server_error", "detail": str(e)}), 500
