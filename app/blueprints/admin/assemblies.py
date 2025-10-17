# app/blueprints/admin/assemblies.py
from flask import render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func

from . import bp  # the single admin blueprint

from app.extensions import db
from app.models.assembly import Assembly, AssemblyComponent
from app.models.material import Material

from app.services.assemblies import (
    ServiceError,
    list_assemblies as svc_list_assemblies,
    get_assembly as svc_get_assembly,
    create_assembly as svc_create_assembly,
    update_assembly as svc_update_assembly,
    set_assembly_active as svc_set_assembly_active,
    hard_delete_assembly as svc_hard_delete_assembly,
    list_components as svc_list_components,
    add_component as svc_add_component,
    update_component as svc_update_component,
    set_component_active as svc_set_component_active,
)


@bp.get("/assemblies")
def list_assemblies():
    # Rows for the table
    rows = (
        Assembly.query
        .order_by(func.lower(Assembly.name).asc())
        .all()
    )

    # Build categories (DISTINCT first, then ORDER BY lower(...) in outer query)
    cat_subq = (
        db.session.query(Assembly.category.label("category"))
        .filter(Assembly.category.isnot(None), Assembly.category != "")
        .distinct()
        .subquery()
    )
    cat_rows = (
        db.session.query(cat_subq.c.category)
        .order_by(func.lower(cat_subq.c.category).asc())
        .all()
    )
    categories = [r[0] for r in cat_rows if r[0]]

    # Build { category: [sub1, sub2, ...] } map for the Inline Add Subcategory <select>
    pair_subq = (
        db.session.query(
            Assembly.category.label("category"),
            Assembly.subcategory.label("subcategory"),
        )
        .filter(
            Assembly.category.isnot(None), Assembly.category != "",
            Assembly.subcategory.isnot(None), Assembly.subcategory != "",
        )
        .distinct()
        .subquery()
    )
    pair_rows = (
        db.session.query(pair_subq.c.category, pair_subq.c.subcategory)
        .order_by(
            func.lower(pair_subq.c.category).asc(),
            func.lower(pair_subq.c.subcategory).asc(),
        )
        .all()
    )
    asm_subcats_map = {}
    for cat, sub in pair_rows:
        asm_subcats_map.setdefault(cat, []).append(sub)
        
    # Material categories (case-insensitive sorted)
    mat_type_subq = (
        db.session.query(Material.material_type.label("type"))
        .filter(Material.material_type.isnot(None), Material.material_type != "")
        .distinct()
        .subquery()
    )
    type_rows = (
        db.session.query(mat_type_subq.c.type)
        .order_by(func.lower(mat_type_subq.c.type).asc())
        .all()
    )
    mat_types = [r[0] for r in type_rows if r[0]]

    # Materials (id, type, description) — used by the modal Description dropdown
    materials = (
        db.session.query(
            Material.id,
            Material.material_type,          # <-- include type
            Material.item_description,
        )
        .order_by(
            func.lower(Material.material_type).asc(),
            func.lower(Material.item_description).asc(),
        )
        .all()
    )

    return render_template(
        "admin/assemblies_index.html",
        rows=rows,
        categories=categories,
        asm_subcats_map=asm_subcats_map,
        materials=materials,
        mat_types=mat_types,
    )

@bp.get("/assemblies/new")
def new_assembly():
    return render_template("admin/assemblies_new.html")


@bp.post("/assemblies")
def create_assembly():
    name = (request.form.get("name") or "").strip()
    try:
        asm = svc_create_assembly(
            db.session,
            name=name,
            notes=(request.form.get("notes") or "").strip() or None,
            assembly_code=(request.form.get("assembly_code") or "").strip() or None,
            category=(request.form.get("category") or "").strip() or None,
            subcategory=(request.form.get("subcategory") or "").strip() or None,
            is_featured=(request.form.get("is_featured") in ("on", "true", "1")),
        )
        db.session.commit()
        flash("Assembly created.", "success")
        return redirect(url_for("admin.list_assemblies"))
    except ServiceError as e:
        db.session.rollback()
        flash(str(e), "error")
        return redirect(url_for("admin.new_assembly"))
    except SQLAlchemyError:
        db.session.rollback()
        flash("Database error creating assembly.", "error")
        return redirect(url_for("admin.new_assembly"))
    
@bp.post("/assemblies/bundle")
def create_assembly_bundle():
    """
    JSON-only endpoint to create an assembly and its components atomically.
    Expected payload:
    {
      "name": "...",
      "category": "...",
      "subcategory": "...",
      "assembly_code": "...",        # optional
      "notes": "...",                # optional
      "is_featured": true/false,
      "is_active": true/false,
      "components": [
        {"material_id": 123, "qty_per_assembly": 4, "sort_order": 1}, ...
      ]
    }
    """
    data = request.get_json(silent=True) or {}
    errors = []

    name = (data.get("name") or "").strip()
    category = (data.get("category") or "").strip()
    subcategory = (data.get("subcategory") or "").strip()
    assembly_code = (data.get("assembly_code") or "").strip()
    notes = (data.get("notes") or "").strip()
    is_featured = bool(data.get("is_featured", False))
    is_active = bool(data.get("is_active", True))
    comps = data.get("components") or []

    if not category:
        errors.append("Category is required.")
    if not subcategory:
        errors.append("Subcategory is required.")
    if not name:
        errors.append("Assembly Name is required.")
    if not comps:
        errors.append("At least one component is required.")

    # validate components
    norm_comps = []
    for idx, c in enumerate(comps, start=1):
        try:
            mid = int(c.get("material_id"))
        except (TypeError, ValueError):
            errors.append(f"Component #{idx}: material_id is invalid.")
            continue
        try:
            qty = int(c.get("qty_per_assembly"))
        except (TypeError, ValueError):
            errors.append(f"Component #{idx}: qty must be a whole number.")
            continue
        if qty <= 0:
            errors.append(f"Component #{idx}: qty must be >= 1.")

        sort_order = c.get("sort_order")
        try:
            sort_order = int(sort_order) if sort_order is not None else None
        except (TypeError, ValueError):
            sort_order = None

        norm_comps.append({"material_id": mid, "qty_per_assembly": qty, "sort_order": sort_order})

    if errors:
        return jsonify({"message": "Validation error", "errors": errors}), 400

    # verify materials exist, build a quick lookup (avoid N queries if you prefer)
    mid_list = [c["material_id"] for c in norm_comps]
    existing_mids = {m[0] for m in db.session.query(Material.id).filter(Material.id.in_(mid_list)).all()}
    for idx, c in enumerate(norm_comps, start=1):
        if c["material_id"] not in existing_mids:
            return jsonify({"message": "Validation error",
                            "errors": [f"Component #{idx}: material does not exist."]}), 400

     # Atomic create (request-scoped transaction; no explicit begin())
    try:
        a = Assembly(
            name=name,
            category=category,
            subcategory=subcategory,
            assembly_code=(assembly_code or None),
            notes=(notes or None),
            is_featured=is_featured,
            is_active=is_active,
        )
        db.session.add(a)
        db.session.flush()  # populate a.id

        # Assign sort orders: use provided or append (1..N)
        next_sort = 0
        for c in norm_comps:
            so = c["sort_order"] if c["sort_order"] is not None else (next_sort + 1)
            next_sort = max(next_sort, so)
            db.session.add(AssemblyComponent(
                assembly_id=a.id,
                material_id=c["material_id"],
                qty_per_assembly=c["qty_per_assembly"],
                sort_order=so,
                is_active=True,
            ))

        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Create failed", "errors": ["Server error while saving assembly and components."]}), 500

    return jsonify({"message": "Created", "id": a.id}), 201

@bp.route("/assemblies/<int:assembly_id>/edit", methods=["GET", "PUT"])
def edit_assembly(assembly_id: int):
    if request.method == "PUT":
        a = db.session.get(Assembly, assembly_id)
        if not a:
            return jsonify({"message": "Not found"}), 404

        data = request.get_json(silent=True) or {}
        errors = []

        name = (data.get("name") or "").strip()
        assembly_code = (data.get("assembly_code") or "").strip()
        notes = (data.get("notes") or "").strip()
        is_featured = bool(data.get("is_featured", False))
        is_active = bool(data.get("is_active", True))

        if not name:
            errors.append("Assembly Name is required.")

        if errors:
            return jsonify({"message": "Validation error", "errors": errors}), 400

        a.name = name
        a.assembly_code = assembly_code or None
        a.notes = notes or None
        a.is_featured = is_featured
        a.is_active = is_active

        db.session.commit()

        return jsonify({
            "message": "Updated",
            "item": {
                "id": a.id,
                "name": a.name,
                "category": a.category,
                "subcategory": a.subcategory,
                "assembly_code": a.assembly_code,
                "notes": a.notes,
                "is_featured": a.is_featured,
                "is_active": a.is_active,
            }
        }), 200

    # --- GET branch (unchanged) ---
    assembly = db.session.get(Assembly, assembly_id)
    if not assembly:
        flash("Assembly not found.", "error")
        return redirect(url_for("admin.list_assemblies"))

    materials = (
        db.session.query(Material.id, Material.item_description)
        .order_by(Material.item_description.asc())
        .all()
    )

    show = (request.args.get("show") or "").strip().lower()
    components = svc_list_components(
        db.session,
        assembly_id=assembly_id,
        include_inactive=(show == "all"),
    )

    open_flag = (request.args.get("open") or "").strip()

    return render_template(
        "admin/assemblies_edit.html",
        assembly=assembly,
        materials=materials,
        components=components,
        open_flag=open_flag,
        show_all=(show == "all"),
    )

@bp.get("/assemblies/<int:assembly_id>/components.json")
def components_json(assembly_id: int):
    rows = (
        db.session.query(
            AssemblyComponent.id,
            AssemblyComponent.material_id,
            Material.item_description,
            AssemblyComponent.qty_per_assembly,
            AssemblyComponent.sort_order,
            AssemblyComponent.is_active,
        )
        .join(Material, Material.id == AssemblyComponent.material_id)
        .filter(AssemblyComponent.assembly_id == assembly_id)
        .order_by(AssemblyComponent.sort_order.asc(), Material.item_description.asc())
        .all()
    )
    data = [
        {
            "id": r[0],
            "material_id": r[1],
            "material_name": r[2],
            "qty_per_assembly": r[3],
            "sort_order": r[4],
            "is_active": r[5],
        }
        for r in rows
    ]
    return jsonify(data), 200

@bp.post("/assemblies/<int:assembly_id>/components")
def add_component(assembly_id: int):
    assembly = db.session.get(Assembly, assembly_id)
    if not assembly:
        flash("Assembly not found.", "error")
        return redirect(url_for("admin.new_assembly"))

    try:
        material_id = int((request.form.get("material_id") or "0").strip() or "0")
    except ValueError:
        material_id = 0

    qty_raw = (request.form.get("qty_per_assembly") or "").strip()
    sort_raw = (request.form.get("sort_order") or "").strip()

    errs = []
    if material_id <= 0:
        errs.append("Material is required.")
    try:
        qty_per_assembly = int(qty_raw)
        if qty_per_assembly <= 0:
            errs.append("Quantity must be > 0.")
    except Exception:
        errs.append("Quantity must be a number > 0.")

    sort_order = None
    if sort_raw != "":
        try:
            sort_order = int(sort_raw)
        except Exception:
            errs.append("Sort order must be an integer.")

    if errs:
        for m in errs:
            flash(m, "error")
        return redirect(url_for("admin.list_assemblies"))

    try:
        svc_add_component(
            db.session,
            assembly_id=assembly_id,
            material_id=material_id,
            qty_per_assembly=qty_per_assembly,
            sort_order=sort_order,
        )
        db.session.commit()
        flash("Component added.", "success")
    except ServiceError as e:
        db.session.rollback()
        flash(str(e), "error")
    except SQLAlchemyError:
        db.session.rollback()
        flash("Database error adding component.", "error")

    return redirect(url_for("admin.list_assemblies"))


@bp.post("/assemblies/<int:assembly_id>/delete")
def delete_assembly(assembly_id: int):
    a = db.session.get(Assembly, assembly_id)
    if not a:
        flash("Assembly not found.", "error")
        return redirect(url_for("admin.list_assemblies"))

    try:
        # 1) Remove all components for this assembly so hard delete can proceed
        db.session.query(AssemblyComponent).filter(
            AssemblyComponent.assembly_id == assembly_id
        ).delete(synchronize_session=False)
        db.session.flush()  # ensure rows are gone before assembly delete

        # 2) Now hard delete the assembly (service keeps the rules/side-effects)
        svc_hard_delete_assembly(db.session, assembly_id=assembly_id)
        db.session.commit()

        flash("Assembly and its components deleted.", "success")
    except ServiceError as e:
        db.session.rollback()
        # If the service still blocks (e.g., referenced elsewhere), keep the message.
        flash(str(e), "error")
    except SQLAlchemyError:
        db.session.rollback()
        flash("Database error while deleting.", "error")

    return redirect(url_for("admin.list_assemblies"))

@bp.post("/assemblies/<int:assembly_id>/components/<int:component_id>/deactivate")
def deactivate_component(assembly_id: int, component_id: int):
    comp = db.session.get(AssemblyComponent, component_id)
    if not comp or comp.assembly_id != assembly_id:
        flash("Component not found.", "error")
        return redirect(url_for("admin.list_assemblies"))
    try:
        svc_set_component_active(db.session, component_id=component_id, active=False)
        db.session.commit()
        flash("Component deactivated.", "success")
    except ServiceError as e:
        db.session.rollback()
        flash(str(e), "error")
    except SQLAlchemyError:
        db.session.rollback()
        flash("Database error updating component.", "error")
    show = request.args.get("show") or ""
    return redirect(url_for("admin.list_assemblies", assembly_id=assembly_id, show=show))


@bp.post("/assemblies/<int:assembly_id>/components/<int:component_id>/activate")
def activate_component(assembly_id: int, component_id: int):
    comp = db.session.get(AssemblyComponent, component_id)
    if not comp or comp.assembly_id != assembly_id:
        flash("Component not found.", "error")
        return redirect(url_for("admin.list_assemblies", assembly_id=assembly_id))
    try:
        svc_set_component_active(db.session, component_id=component_id, active=True)
        db.session.commit()
        flash("Component reactivated.", "success")
    except ServiceError as e:
        db.session.rollback()
        flash(str(e), "error")
    except SQLAlchemyError:
        db.session.rollback()
        flash("Database error updating component.", "error")
    show = request.args.get("show") or ""
    return redirect(url_for("admin.list_assemblies", assembly_id=assembly_id, show=show))

