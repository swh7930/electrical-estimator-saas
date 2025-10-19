from flask import render_template, request, jsonify, redirect, url_for
from sqlalchemy import func, or_
from datetime import datetime
from . import bp
from app.extensions import db
from app.models.estimate import Estimate
from app.models.app_settings import AppSettings
from app.models.customer import Customer

@bp.get("/")
def index():
    return render_template("estimates/index.html")

@bp.get("/new")
def new():
    return render_template("estimates/new_standard.html")

@bp.post("/")
def create():
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Estimate name is required."}), 400

    # Optional fields
    def _s(v): 
        v = (v or "").strip()
        return v or None

    customer_id = data.get("customer_id")
    try:
        customer_id = int(customer_id) if str(customer_id or "").isdigit() else None
    except Exception:
        customer_id = None

    # Snapshot Admin → Settings at creation time
    srow = db.session.get(AppSettings, 1)
    snapshot = (srow.settings if srow and isinstance(srow.settings, dict) else {})

    est = Estimate(
        name=name,
        customer_id=customer_id,
        project_address=_s(data.get("project_address")),
        project_ref=_s(data.get("project_ref")),
        status="draft",
        settings_snapshot=snapshot,
    )
    db.session.add(est)
    db.session.commit()

    # JSON response for fetch() caller; front-end will navigate
    return jsonify({"id": est.id})

@bp.get("/list.json")
def list_json():
    q = (request.args.get("q") or "").strip()
    customer_id = (request.args.get("customer_id") or "").strip()
    status = (request.args.get("status") or "").strip().lower()
    updated_from = (request.args.get("updated_from") or "").strip()

    query = db.session.query(Estimate, Customer.company_name).select_from(Estimate).outerjoin(Customer, Estimate.customer_id == Customer.id)

    if q:
        like = f"%{q.lower()}%"
        query = query.filter(or_(
            func.lower(Estimate.name).like(like),
            func.lower(Estimate.project_ref).like(like),
        ))
    if customer_id.isdigit():
        query = query.filter(Estimate.customer_id == int(customer_id))
    if status in ("draft", "submitted", "awarded", "lost"):
        query = query.filter(func.lower(Estimate.status) == status)
    if updated_from:
        try:
            dt = datetime.strptime(updated_from, "%Y-%m-%d")
            query = query.filter(Estimate.updated_at >= dt)
        except Exception:
            pass

    rows = query.order_by(Estimate.updated_at.desc()).limit(500).all()

    data = [{
        "id": e.id,
        "name": e.name,
        "customer_id": e.customer_id,
        "customer_name": cname,
        "status": e.status,
        "created_at": e.created_at.isoformat() if e.created_at else None,
        "updated_at": e.updated_at.isoformat() if e.updated_at else None,
    } for (e, cname) in rows]

    return jsonify(ok=True, rows=data)

@bp.post("/<int:estimate_id>/clone")
def clone_estimate(estimate_id: int):
    e = Estimate.query.get_or_404(estimate_id)
    copy = Estimate(
        name=f"{e.name} (copy)" if e.name else "Copy",
        customer_id=e.customer_id,
        project_address=e.project_address,
        project_ref=e.project_ref,
        status="draft",
        settings_snapshot=e.settings_snapshot or {},
    )
    db.session.add(copy)
    db.session.commit()
    return jsonify(ok=True, id=copy.id)

@bp.delete("/<int:estimate_id>")
def delete_estimate(estimate_id: int):
    e = Estimate.query.get_or_404(estimate_id)
    db.session.delete(e)
    db.session.commit()
    return ("", 204)


@bp.get("/fast")
def fast():
    return render_template("estimates/fast.html")  # stub for later

@bp.get("/<int:estimate_id>")
def view(estimate_id):
    return render_template("estimates/view.html", estimate_id=estimate_id)  # stub for later
