from flask import render_template, request, jsonify, url_for, redirect, request, abort, session
from sqlalchemy import func, or_
from app.models.material import Material
from app.models.dje_item import DjeItem
from app.models.customer import Customer
from app.models.org_membership import OrgMembership, ROLE_ADMIN, ROLE_OWNER
from app.extensions import db, limiter
from sqlalchemy.exc import IntegrityError
from app.utils.validators import (
    clean_str,
    is_valid_email,
    normalize_phone,
    is_valid_city,
    derive_city_from_address,
    is_valid_state,
    is_valid_zip
)
from . import bp
from flask_login import current_user
from app.services.policy import require_member, role_required

@bp.before_request
def _acl_libraries_readonly_for_members():
    # Require login
    if not getattr(current_user, "is_authenticated", False):
        abort(401)
    # Resolve org
    org_id = session.get("current_org_id") or getattr(current_user, "org_id", None)
    if not org_id:
        abort(401)
    # Membership check
    m = db.session.query(OrgMembership).filter_by(org_id=org_id, user_id=current_user.id).one_or_none()
    if not m:
        abort(404)  # anti-enumeration
    # Writes require admin/owner; reads allowed for members
    if request.method not in ("GET", "HEAD", "OPTIONS") and m.role not in (ROLE_ADMIN, ROLE_OWNER):
        abort(403)


@bp.before_request
def _require_login_libraries():
    if current_user.is_authenticated:
        return None
    return redirect(url_for("auth.login_get", next=request.url))

@require_member
@bp.get("/materials")
def materials():
    # Basic filters (optional)
    q = (request.args.get("q") or "").strip()
    mat_type = (request.args.get("type") or "").strip()

    query = Material.query
    query = query.filter(Material.org_id == current_user.org_id)

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
            .filter(Material.org_id == current_user.org_id, Material.material_type.isnot(None))
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

@role_required(ROLE_ADMIN, ROLE_OWNER)
@bp.post("/materials")
@limiter.limit("120 per minute")
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
    
    m.org_id = current_user.org_id

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

@role_required(ROLE_ADMIN, ROLE_OWNER)
@bp.route("/materials/<int:material_id>", methods=["DELETE"])
def materials_delete(material_id: int):
    m = Material.query.filter_by(id=material_id, org_id=current_user.org_id).first_or_404()
    db.session.delete(m)
    db.session.commit()
    return jsonify(ok=True), 204

@role_required(ROLE_ADMIN, ROLE_OWNER)
@bp.route("/materials/<int:material_id>", methods=["PUT"])
def materials_update(material_id: int):
    m = Material.query.filter_by(id=material_id, org_id=current_user.org_id).first_or_404()
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

@require_member
@bp.get("/dje")
def dje():
    items = (
        DjeItem.query
        .filter(DjeItem.org_id == current_user.org_id)
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
        .filter(DjeItem.org_id == current_user.org_id, DjeItem.category.isnot(None))
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
        .filter(
            DjeItem.org_id == current_user.org_id,
            DjeItem.category.isnot(None),
            DjeItem.subcategory.isnot(None),
        )
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

@role_required(ROLE_ADMIN, ROLE_OWNER)
@bp.post("/dje")
@limiter.limit("120 per minute")
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
    item.org_id = current_user.org_id
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

@role_required(ROLE_ADMIN, ROLE_OWNER)
@bp.put("/dje/<int:item_id>")
@limiter.limit("120 per minute")
def update_dje(item_id):
    item = DjeItem.query.filter_by(id=item_id, org_id=current_user.org_id).first_or_404()
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

@role_required(ROLE_ADMIN, ROLE_OWNER)
@bp.delete("/dje/<int:item_id>")
@limiter.limit("120 per minute")
def delete_dje(item_id):
    item = DjeItem.query.filter_by(id=item_id, org_id=current_user.org_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return ("", 204)

@require_member
@bp.get("/customers")
def customers():
    q = (request.args.get("q") or "").strip()
    city = (request.args.get("city") or "").strip()
    active = (request.args.get("active") or "true").strip().lower()  # true|false|all

    query = Customer.query
    query = query.filter(Customer.org_id == current_user.org_id)
    if active in ("true", "false"):
        query = query.filter(Customer.is_active.is_(active == "true"))

    if q:
        pattern = f"%{q.lower()}%"
        query = query.filter(or_(
            func.lower(Customer.company_name).like(pattern),
            func.lower(Customer.contact_name).like(pattern),
            func.lower(Customer.email).like(pattern),
        ))

    if city:
        query = query.filter(func.lower(Customer.city).like(f"%{city.lower()}%"))

    items = query.order_by(func.lower(Customer.company_name).asc()).limit(250).all()

    # Back-link handoff (same pattern you use elsewhere)
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
        active_filter=active,
        back_label=back_label,
        back_href=back_href,
        rt=rt,
    )
   
@require_member 
@bp.get("/customers.json")
def customers_json():
    q = (request.args.get("q") or "").strip()
    active = (request.args.get("active") or "true").strip().lower()

    query = Customer.query
    query = query.filter(Customer.org_id == current_user.org_id)
    if active in ("true", "false"):
        query = query.filter(Customer.is_active.is_(active == "true"))

    if q:
        pattern = f"%{q.lower()}%"
        query = query.filter(or_(
            func.lower(Customer.company_name).like(pattern),
            func.lower(Customer.contact_name).like(pattern),
            func.lower(Customer.email).like(pattern),
        ))

    rows = query.order_by(func.lower(Customer.company_name).asc()).limit(500).all()
    data = [{
        "id": c.id,
        "company_name": c.company_name,
        "contact_name": c.contact_name,
        "email": c.email,
        "phone": c.phone,
        "address1": c.address1,
        "address2": c.address2,
        "city": c.city,
        "state": c.state,
        "zip": c.zip,
        "notes": c.notes,
        "is_active": bool(c.is_active),
    } for c in rows]
    return jsonify(ok=True, rows=data)

@role_required(ROLE_ADMIN, ROLE_OWNER)
@bp.post("/customers")
@limiter.limit("120 per minute")
def customers_create():
    data = request.get_json(silent=True) or {}
    errors = {}

    company_name = clean_str(data.get("company_name"), 255)
    if not company_name:
        errors["company_name"] = "Company Name is required."

    contact_name = clean_str(data.get("contact_name"), 255)
    email_raw = clean_str(data.get("email"), 255)
    phone_raw = clean_str(data.get("phone"), 32)
    address1 = clean_str(data.get("address1"), 255)
    address2 = clean_str(data.get("address2"), 255)
    city = clean_str(data.get("city"), 100)
    state = clean_str(data.get("state"), 2)
    zip_code = clean_str(data.get("zip"), 10)
    notes = clean_str(data.get("notes"), 2000)
    is_active = bool(data.get("is_active")) if "is_active" in data else True

    if email_raw and not is_valid_email(email_raw):
        errors["email"] = "Invalid email address."

    phone = None
    if phone_raw:
        phone = normalize_phone(phone_raw)
        if not phone:
            errors["phone"] = "Invalid US phone number. Use 10 digits (optionally prefixed with 1)."

    if not city and address1:
        city = derive_city_from_address(address1)
    if city and not is_valid_city(city):
        errors["city"] = "City contains invalid characters."

    if state and not is_valid_state(state):
        errors["state"] = "State must be 2 letters."
    if zip_code and not is_valid_zip(zip_code):
        errors["zip"] = "ZIP must be 12345 or 12345-1234."

    if errors:
        return jsonify(ok=False, errors=errors), 400

    c = Customer(
        company_name=company_name, contact_name=contact_name, email=email_raw, phone=phone,
        address1=address1, address2=address2, city=city, state=state, zip=zip_code,
        notes=notes, is_active=is_active
    )
    c.user_id = current_user.id
    c.org_id = current_user.org_id
    db.session.add(c)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(ok=False, errors={"__all__": "Could not save (conflict)."}), 409

    return jsonify(ok=True, id=c.id), 201

@role_required(ROLE_ADMIN, ROLE_OWNER)
@bp.put("/customers/<int:customer_id>")
@limiter.limit("120 per minute")
def customers_update(customer_id: int):
    c = Customer.query.filter_by(id=customer_id, org_id=current_user.org_id).first_or_404()
    data = request.get_json(silent=True) or {}
    errors = {}

    def set_clean(attr, key, max_len=255):
        if key in data:
            setattr(c, attr, clean_str(data.get(key), max_len))

    if "company_name" in data:
        cn = clean_str(data.get("company_name"), 255)
        if not cn:
            errors["company_name"] = "Company Name is required."
        else:
            c.company_name = cn

    set_clean("contact_name", "contact_name")
    set_clean("email", "email")
    if c.email and not is_valid_email(c.email):
        errors["email"] = "Invalid email address."

    if "phone" in data:
        pr = clean_str(data.get("phone"), 32)
        c.phone = normalize_phone(pr) if pr else None
        if pr and not c.phone:
            errors["phone"] = "Invalid US phone number. Use 10 digits (optionally prefixed with 1)."

    set_clean("address1", "address1")
    set_clean("address2", "address2")
    set_clean("city", "city", 100)
    if c.city and not is_valid_city(c.city):
        errors["city"] = "City contains invalid characters."

    set_clean("state", "state", 2)
    if c.state and not is_valid_state(c.state):
        errors["state"] = "State must be 2 letters."

    set_clean("zip", "zip", 10)
    if c.zip and not is_valid_zip(c.zip):
        errors["zip"] = "ZIP must be 12345 or 12345-1234."

    set_clean("notes", "notes", 2000)

    if "is_active" in data:
        c.is_active = bool(data.get("is_active"))

    if errors:
        return jsonify(ok=False, errors=errors), 400

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(ok=False, errors={"__all__": "Could not save (conflict)."}), 409

    return jsonify(ok=True), 200

@role_required(ROLE_ADMIN, ROLE_OWNER)
@bp.post("/customers/<int:customer_id>/toggle_active")
@limiter.limit("120 per minute")
def customers_toggle_active(customer_id: int):
    c = Customer.query.filter_by(id=customer_id, org_id=current_user.org_id).first_or_404()
    c.is_active = not bool(c.is_active)
    db.session.commit()
    return jsonify(ok=True, is_active=bool(c.is_active))

@role_required(ROLE_ADMIN, ROLE_OWNER)
@bp.delete("/customers/<int:customer_id>")
@limiter.limit("120 per minute")
def customers_delete(customer_id: int):
    c = Customer.query.filter_by(id=customer_id, org_id=current_user.org_id).first_or_404()
    db.session.delete(c)
    db.session.commit()
    return ("", 204)
