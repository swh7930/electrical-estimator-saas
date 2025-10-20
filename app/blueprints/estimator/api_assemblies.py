from flask import jsonify, request, current_app
from . import bp
from flask_login import current_user
from app.extensions import db
from app.services.assemblies import (
    list_assemblies as svc_list_assemblies,
    get_assembly_rollup as svc_get_assembly_rollup,
)
from app.services.assemblies import ServiceError

@bp.get("/api/assemblies")
def get_assemblies():
    """Return active assemblies for the Estimator (flat list)."""
    try:
        q = (request.args.get("q") or "").strip() or None
        category = (request.args.get("category") or "").strip() or None
        subcategory = (request.args.get("subcategory") or "").strip() or None

        page = svc_list_assemblies(
            db.session,
            active_only=True,
            category=category,
            subcategory=subcategory,
            q=q,
            org_id=current_user.org_id,
            limit=500,
            offset=0,
        )

        result = [
            {
                "id": asm.id,
                "name": asm.name,
                # Shape for populateDescSelect():
                "item_description": asm.name,
                "category": asm.category,
                "subcategory": asm.subcategory,
                "is_active": asm.is_active,
            }
            for asm in page.items
        ]
        return jsonify(result), 200
    except Exception as e:
        current_app.logger.exception("GET /api/assemblies failed")
        return jsonify({"error": "server_error", "detail": str(e)}), 500


@bp.get("/api/assemblies/<int:assembly_id>/rollup")
def get_assembly_rollup(assembly_id: int):
    """Return per-each totals for an assembly: material_cost_total, labor_hours_total."""
    try:
        data = svc_get_assembly_rollup(assembly_id, org_id=current_user.org_id)
        return jsonify(
            {
                "assembly_id": data["assembly_id"],
                "material_cost_total": float(data["material_cost_total"]),
                "labor_hours_total": float(data["labor_hours_total"]),
                "component_count": data["component_count"],
            }
        ), 200
        
    except ServiceError as se:
        return jsonify({"error": "not_found"}), 404
    
    except Exception as e:
        current_app.logger.exception("GET /api/assemblies/<id>/rollup failed")
        return jsonify({"error": "server_error", "detail": str(e)}), 500
