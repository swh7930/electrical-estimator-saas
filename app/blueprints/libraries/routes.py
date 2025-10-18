from flask import render_template, request, jsonify, url_for
from sqlalchemy import func, or_
from app.models.material import Material
from app.models.dje_item import DjeItem
from app.models.customer import Customer
from app.extensions import db
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, or_
from app.utils.validators import (
    clean_str,
    is_valid_email,
    normalize_phone,
    is_valid_city,
    derive_city_from_address,
)
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
    
    # Back-link handoff
    rt = (request.args.get("rt") or "").strip()
    back_label = None
    back_href = None
    if rt == "home":
        back_label = "Back to Home"
        back_href = url_for("main.home")
    elif rt.startswith("estimator"):
        back_label = "Back to Estimate"

    return render_template(
        "materials/index.html",
        materials=items,
        mat_types=mat_types,
        q=q,
        type_filter=mat_type,
        back_label=back_label,
        back_href=back_href,
        rt=rt,
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
    items = (
        DjeItem.query
        .order_by(
            func.lower(DjeItem.category).asc(),
            func.lower(DjeItem.subcategory).asc(),
            func.lower(DjeItem.description).asc(),
        )
        .all()
    )

    # Catalogs for Inline Add suggestions
     # DISTINCT first (subquery), then ORDER BY LOWER(...) on the outer query (DB-side)
    cat_subq = (
        db.session.query(DjeItem.category.label("category"))
        .filter(DjeItem.category.isnot(None))
        .distinct()
        .subquery()
    )
    cat_rows = (
        db.session.query(cat_subq.c.category)
        .order_by(func.lower(cat_subq.c.category).asc())
        .all()
    )
    categories = [r[0] for r in cat_rows if r[0]]

    pair_subq = (
        db.session.query(
            DjeItem.category.label("category"),
            DjeItem.subcategory.label("subcategory"),
        )
        .filter(DjeItem.category.isnot(None), DjeItem.subcategory.isnot(None))
        .distinct()
        .subquery()
    )
    sub_pairs = (
        db.session.query(pair_subq.c.category, pair_subq.c.subcategory)
        .order_by(
            func.lower(pair_subq.c.category).asc(),
            func.lower(pair_subq.c.subcategory).asc(),
        )
        .all()
    )

    dje_subcats_map = {}
    for cat, sub in sub_pairs:
        dje_subcats_map.setdefault(cat, []).append(sub)
        
    # Back-link handoff
    rt = (request.args.get("rt") or "").strip()
    back_label = None
    back_href = None
    if rt == "home":
        back_label = "Back to Home"
        back_href = url_for("main.home")
    elif rt.startswith("estimator"):
        back_label = "Back to Estimate"

    return render_template(
        "dje/index.html",
        items=items,
        dje_categories=categories,
        dje_subcats_map=dje_subcats_map,
        back_label=back_label,
        back_href=back_href,
        rt=rt,
    )

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
    if not subcategory:
        errors.append("Subcategory is required.")
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

@bp.put("/dje/<int:item_id>")
def update_dje(item_id):
    item = DjeItem.query.get_or_404(item_id)
    data = request.get_json(silent=True) or {}
    errors = []

    description = (data.get("description") or "").strip()
    cost_raw = data.get("default_unit_cost")
    cost_code = (data.get("cost_code") or "").strip()
    is_active = bool(data.get("is_active", True))

    if not description:
        errors.append("Description is required.")
    try:
        unit_cost = round(float(cost_raw), 2)
    except (TypeError, ValueError):
        errors.append("Unit Cost must be a valid number.")

    if errors:
        return jsonify({"message": "Validation error", "errors": errors}), 400

    # Category/Subcategory locked (match Materials behavior)
    item.description = description
    item.default_unit_cost = unit_cost
    item.cost_code = cost_code or None
    item.is_active = is_active

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "message": "Duplicate DJE item.",
            "errors": ["A DJE item with these details already exists."]
        }), 409

    return jsonify({
        "message": "Updated",
        "item": {
            "id": item.id,
            "category": item.category,
            "subcategory": item.subcategory,
            "description": item.description,
            "default_unit_cost": float(item.default_unit_cost or 0),
            "cost_code": item.cost_code,
            "is_active": item.is_active,
        }
    }), 200


@bp.delete("/dje/<int:item_id>")
def delete_dje(item_id):
    item = DjeItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return ("", 204)




@bp.get("/customers")
def customers():
    q = (request.args.get("q") or "").strip()
    city = (request.args.get("city") or "").strip()

    query = Customer.query.filter(Customer.is_active.is_(True))

    if q:
        pattern = f"%{q.lower()}%"
        query = query.filter(
            or_(
                func.lower(Customer.name).like(pattern),
                func.lower(Customer.primary_contact).like(pattern),
                func.lower(Customer.email).like(pattern),
            )
        )
    if city:
        query = query.filter(func.lower(Customer.city).like(f"%{city.lower()}%"))

    items = query.order_by(func.lower(Customer.name).asc()).limit(250).all()

    # Back-link handoff (parity with Materials/DJE)
    rt = (request.args.get("rt") or "").strip()
    back_label = None
    back_href = None
    if rt == "home":
        back_label = "Back to Home"
        back_href = url_for("main.home")
    elif rt.startswith("estimator"):
        back_label = "Back to Estimate"

    return render_template(
        "customers/index.html",
        customers=items,
        q=q,
        city_filter=city,
        back_label=back_label,
        back_href=back_href,
        rt=rt,
    )

@bp.post("/customers")
def customers_create():
    data = request.get_json(silent=True) or {}
    errors = {}

    # Required
    name = clean_str(data.get("name"), 255)
    if not name:
        errors["name"] = "Customer Name is required."

    # Optional, cleaned
    primary_contact = clean_str(data.get("primary_contact"), 255)
    email_raw = clean_str(data.get("email"), 255)
    phone_raw = clean_str(data.get("phone"), 32)
    address = clean_str(data.get("address"), 300)
    notes = clean_str(data.get("notes"), 2000)
    city = clean_str(data.get("city"), 100)

    # Email
    if email_raw and not is_valid_email(email_raw):
        errors["email"] = "Invalid email address."

    # Phone (normalize to (###) ###-####)
    phone = None
    if phone_raw:
        phone = normalize_phone(phone_raw)
        if not phone:
            errors["phone"] = "Invalid US phone number. Use 10 digits (optionally prefixed with 1)."

    # City (use provided else derive from address)
    if not city and address:
        city = derive_city_from_address(address)
    if city and not is_valid_city(city):
        errors["city"] = "City contains invalid characters."

    if errors:
        return jsonify(ok=False, errors=errors), 400

    c = Customer(
        name=name,
        primary_contact=primary_contact,
        email=email_raw,
        phone=phone,
        address=address,
        city=city,
        notes=notes,
        is_active=True,
    )
    db.session.add(c)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(ok=False, errors={"__all__": "A customer with this name already exists (active)."}), 409

    return jsonify(ok=True, id=c.id), 201

@bp.put("/customers/<int:customer_id>")
def customers_update(customer_id: int):
    c = Customer.query.get_or_404(customer_id)
    data = request.get_json(silent=True) or {}
    errors = {}

    # Only validate fields that were provided
    if "name" in data:
        name = clean_str(data.get("name"), 255)
        if not name:
            errors["name"] = "Customer Name is required."
        else:
            c.name = name

    if "primary_contact" in data:
        c.primary_contact = clean_str(data.get("primary_contact"), 255)

    if "email" in data:
        email_raw = clean_str(data.get("email"), 255)
        if email_raw and not is_valid_email(email_raw):
            errors["email"] = "Invalid email address."
        else:
            c.email = email_raw

    if "phone" in data:
        phone_raw = clean_str(data.get("phone"), 32)
        phone = normalize_phone(phone_raw) if phone_raw else None
        if phone_raw and not phone:
            errors["phone"] = "Invalid US phone number. Use 10 digits (optionally prefixed with 1)."
        else:
            c.phone = phone

    if "address" in data:
        c.address = clean_str(data.get("address"), 300)

    if "notes" in data:
        c.notes = clean_str(data.get("notes"), 2000)

    if "city" in data:
        city = clean_str(data.get("city"), 100)
        if city and not is_valid_city(city):
            errors["city"] = "City contains invalid characters."
        else:
            c.city = city

    # If city wasn't provided but address changed, consider deriving (optional)
    # Not auto-deriving on update unless explicitly requested—keeps surprises minimal.

    if errors:
        return jsonify(ok=False, errors=errors), 400

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(ok=False, errors={"__all__": "A customer with this name already exists (active)."}), 409

    return jsonify(ok=True), 200

@bp.delete("/customers/<int:customer_id>")
def customers_delete(customer_id: int):
    c = Customer.query.get_or_404(customer_id)
    db.session.delete(c)
    db.session.commit()
    return ("", 204)
