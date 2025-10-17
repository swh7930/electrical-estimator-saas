from flask import render_template, request, jsonify
from sqlalchemy import func
from app.models.material import Material
from app.models.dje_item import DjeItem
from app.extensions import db
from . import bp
from sqlalchemy.exc import IntegrityError

@bp.get("/materials")
def materials():
    # Basic filters (optional)
    q = (request.args.get("q") or "").strip()
    mat_type = (request.args.get("type") or "").strip()

    query = Material.query

    if mat_type:
        query = query.filter(Material.material_type == mat_type)

    if q:
        like = f"%{q}%"
        query = query.filter(
            (Material.item_description.ilike(like))
            | (Material.sku.ilike(like))
            | (Material.manufacturer.ilike(like))
            | (Material.vendor.ilike(like))
        )   

    # Order by description for stable display
    items = query.order_by(
        func.lower(Material.material_type).asc(),
        func.lower(Material.item_description).asc(),
    ).all()

    mat_types = [
        row[0]
        for row in (
            db.session.query(Material.material_type)
            .filter(Material.material_type.isnot(None))
            .distinct()
            .order_by(Material.material_type.asc())
            .all()
        )
    ]

    return render_template(
        "materials/index.html",
        materials=items,
        mat_types=mat_types,
        q=q,
        type_filter=mat_type,
    )


@bp.post("/materials")
def materials_create():
    """
    Accepts JSON from fetch() and creates a Material.
    Required: material_type, item_description, price, labor_unit, unit_quantity_size in {1,100,1000}
    Optional: sku, manufacturer, vendor, material_cost_code, mat_cost_code_desc, labor_cost_code, labor_cost_code_desc, is_active
    Returns: { ok: True, id: <new_id> }
    """
    data = request.get_json(silent=True) or {}
    # Pull & normalize fields
    material_type = (data.get("material_type") or "").strip()
    item_description = (data.get("item_description") or "").strip()
    price = data.get("price")
    labor_unit = data.get("labor_unit")
    unit_quantity_size = data.get("unit_quantity_size")

    # Validate required
    errors = {}
    if not material_type:
        errors["material_type"] = "Category is required."
    if not item_description:
        errors["item_description"] = "Description is required."
    try:
        price = round(float(price), 2)
        if price < 0:
            raise ValueError()
    except Exception:
        errors["price"] = "Price must be a non-negative number with 2 decimals."
    try:
        labor_unit = round(float(labor_unit), 2)
        if labor_unit < 0:
            raise ValueError()
    except Exception:
        errors["labor_unit"] = (
            "Labor Unit must be a non-negative number with 2 decimals."
        )
    try:
        unit_quantity_size = int(unit_quantity_size)
        if unit_quantity_size not in (1, 100, 1000):
            raise ValueError()
    except Exception:
        errors["unit_quantity_size"] = "Unit Qty Size must be 1, 100, or 1000."

    if errors:
        return jsonify(ok=False, errors=errors), 400

    m = Material(
        material_type=material_type,
        item_description=item_description,
        price=price,
        labor_unit=labor_unit,
        unit_quantity_size=unit_quantity_size,
        sku=(data.get("sku") or "").strip() or None,
        manufacturer=(data.get("manufacturer") or "").strip() or None,
        vendor=(data.get("vendor") or "").strip() or None,
        material_cost_code=(data.get("material_cost_code") or "").strip() or None,
        mat_cost_code_desc=(data.get("mat_cost_code_desc") or "").strip() or None,
        labor_cost_code=(data.get("labor_cost_code") or "").strip() or None,
        labor_cost_code_desc=(data.get("labor_cost_code_desc") or "").strip() or None,
        is_active=bool(data.get("is_active", True)),
    )
    db.session.add(m)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(
            ok=False,
            errors={"__all__": "A material with this Category and Description already exists (active)."}
        ), 409
    return jsonify(ok=True, id=m.id), 201

@bp.route("/materials/<int:material_id>", methods=["DELETE"])
def materials_delete(material_id: int):
    m = Material.query.get(material_id)
    if not m:
        return jsonify(ok=False, errors={"__all__": "Material not found."}), 404
    db.session.delete(m)
    db.session.commit()
    return jsonify(ok=True), 204

@bp.route("/materials/<int:material_id>", methods=["PUT"])
def materials_update(material_id: int):
    m = Material.query.get(material_id)
    if not m:
        return jsonify(ok=False, errors={"__all__": "Material not found."}), 404

    data = request.get_json(silent=True) or {}
    # Only updating fields present in the modal
    m.item_description = (data.get("item_description") or "").strip()
    m.price = data.get("price")
    m.labor_unit = data.get("labor_unit")
    m.unit_quantity_size = data.get("unit_quantity_size")

    # simple validation
    if not m.item_description:
        return jsonify(ok=False, errors={"item_description": "Description is required."}), 400
    if m.unit_quantity_size not in (1, 100, 1000):
        return jsonify(ok=False, errors={"unit_quantity_size": "Unit Qty Size must be 1, 100, or 1000."}), 400

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(
            ok=False,
            errors={"__all__": "A material with this Category and Description already exists (active)."}
        ), 409

    return jsonify(ok=True), 200

@bp.get("/dje")
def dje():
    # Simple, consistent listing (same style as Materials)
    items = (
        DjeItem.query
        .order_by(
            func.lower(DjeItem.category).asc(),
            func.lower(DjeItem.subcategory).asc(),
            func.lower(DjeItem.description).asc(),
        )
        .all()
    )
    return render_template("dje/index.html", items=items)

@bp.post("/dje")
def create_dje():
    data = request.get_json(silent=True) or {}
    errors = []

    category = (data.get("category") or "").strip()
    subcategory = (data.get("subcategory") or "").strip()
    description = (data.get("description") or "").strip()
    cost_raw = data.get("default_unit_cost")
    cost_code = (data.get("cost_code") or "").strip()
    is_active = bool(data.get("is_active", True))

    if not category:
        errors.append("Category is required.")
    if not description:
        errors.append("Description is required.")
    try:
        unit_cost = round(float(cost_raw), 2)
    except (TypeError, ValueError):
        errors.append("Unit Cost must be a valid number.")

    if errors:
        return jsonify({"message": "Validation error", "errors": errors}), 400

    item = DjeItem(
        category=category,
        subcategory=subcategory or None,
        description=description,
        default_unit_cost=unit_cost,
        cost_code=cost_code or None,
        is_active=is_active,
    )
    try:
        db.session.add(item)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "message": "Duplicate DJE item.",
            "errors": ["A DJE item with these details already exists."]
        }), 409

    return jsonify({
        "message": "Created",
        "item": {
            "id": item.id,
            "category": item.category,
            "subcategory": item.subcategory,
            "description": item.description,
            "default_unit_cost": float(item.default_unit_cost or 0),
            "cost_code": item.cost_code,
            "is_active": item.is_active,
        }
    }), 201





@bp.get("/customers")
def customers():
    return render_template("customers/index.html")
