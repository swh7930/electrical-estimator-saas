# app/blueprints/admin/assemblies.py
from flask import render_template, request, redirect, url_for, flash
from sqlalchemy.exc import SQLAlchemyError

from . import bp  # the single admin blueprint

from app.extensions import db
from app.models.assembly import Assembly, AssemblyComponent
from app.models.estimate import Material

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
    category = (request.args.get("category") or "").strip() or None
    subcat = (request.args.get("subcategory") or "").strip() or None
    featured = (request.args.get("featured") or "").strip().lower()

    page = svc_list_assemblies(
        db.session,
        active_only=True,
        category=category,
        subcategory=subcat,
        q=(request.args.get("q") or "").strip() or None,
    )
    rows = page.items

    categories = (
        db.session.query(Assembly.category)
        .filter(
            Assembly.is_active.is_(True),
            Assembly.category.isnot(None),
            Assembly.category != "",
        )
        .distinct()
        .order_by(Assembly.category.asc())
        .all()
    )
    subcategories = (
        db.session.query(Assembly.subcategory)
        .filter(
            Assembly.is_active.is_(True),
            Assembly.subcategory.isnot(None),
            Assembly.subcategory != "",
        )
        .distinct()
        .order_by(Assembly.subcategory.asc())
        .all()
    )
    categories = [c[0] for c in categories]
    subcategories = [s[0] for s in subcategories]

    if featured in ("yes", "no"):
        want = (featured == "yes")
        rows = [r for r in rows if bool(r.is_featured) is want]

    return render_template(
        "admin/assemblies_index.html",
        assemblies=rows,
        categories=categories,
        subcategories=subcategories,
        sel_category=category or "",
        sel_subcategory=subcat or "",
        sel_featured=featured,
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
        return redirect(url_for("admin.edit_assembly", assembly_id=asm.id, open="add"))
    except ServiceError as e:
        db.session.rollback()
        flash(str(e), "error")
        return redirect(url_for("admin.new_assembly"))
    except SQLAlchemyError:
        db.session.rollback()
        flash("Database error creating assembly.", "error")
        return redirect(url_for("admin.new_assembly"))


@bp.get("/assemblies/<int:assembly_id>/edit")
def edit_assembly(assembly_id: int):
    assembly = db.session.get(Assembly, assembly_id)
    if not assembly:
        flash("Assembly not found.", "error")
        return redirect(url_for("admin.list_assemblies"))

    materials = (
        db.session.query(Material.id, Material.item_description)
        .order_by(Material.item_description.asc())
        .limit(1000)
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
        qty_per_assembly = float(qty_raw)
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
        return redirect(url_for("admin.edit_assembly", assembly_id=assembly_id))

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

    return redirect(url_for("admin.edit_assembly", assembly_id=assembly_id))


@bp.post("/assemblies/<int:assembly_id>/delete")
def delete_assembly(assembly_id: int):
    a = db.session.get(Assembly, assembly_id)
    if not a:
        flash("Assembly not found.", "error")
        return redirect(url_for("admin.list_assemblies"))

    try:
        svc_hard_delete_assembly(db.session, assembly_id=assembly_id)
        db.session.commit()
        flash("Assembly deleted.", "success")
        return redirect(url_for("admin.list_assemblies"))
    except ServiceError as e:
        db.session.rollback()
        flash(str(e), "error")
        return redirect(url_for("admin.edit_assembly", assembly_id=assembly_id))
    except SQLAlchemyError:
        db.session.rollback()
        flash("Database error while deleting.", "error")
        return redirect(url_for("admin.edit_assembly", assembly_id=assembly_id))


@bp.post("/assemblies/<int:assembly_id>/components/<int:component_id>/deactivate")
def deactivate_component(assembly_id: int, component_id: int):
    comp = db.session.get(AssemblyComponent, component_id)
    if not comp or comp.assembly_id != assembly_id:
        flash("Component not found.", "error")
        return redirect(url_for("admin.edit_assembly", assembly_id=assembly_id))
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
    return redirect(url_for("admin.edit_assembly", assembly_id=assembly_id, show=show))


@bp.post("/assemblies/<int:assembly_id>/components/<int:component_id>/activate")
def activate_component(assembly_id: int, component_id: int):
    comp = db.session.get(AssemblyComponent, component_id)
    if not comp or comp.assembly_id != assembly_id:
        flash("Component not found.", "error")
        return redirect(url_for("admin.edit_assembly", assembly_id=assembly_id))
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
    return redirect(url_for("admin.edit_assembly", assembly_id=assembly_id, show=show))

