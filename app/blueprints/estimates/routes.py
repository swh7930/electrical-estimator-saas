from flask import render_template, request, jsonify, redirect, url_for
from sqlalchemy import func, or_
from datetime import datetime
from . import bp
from flask_login import current_user
from app.extensions import db
from app.models.estimate import Estimate
from app.models.app_settings import AppSettings
from app.models.customer import Customer

@bp.before_request
def _require_login_estimates():
    if current_user.is_authenticated:
        return None
    return redirect(url_for("auth.login_get", next=request.url))


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
    
    est.user_id = current_user.id
    est.org_id = current_user.org_id
    est.work_payload = {}
    
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
    
    query = query.filter(Estimate.org_id == current_user.org_id)

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

@bp.get("/<int:estimate_id>/edit")
def edit(estimate_id: int):
    est = Estimate.query.filter_by(id=estimate_id, org_id=current_user.org_id).first_or_404()
    # Reuse the same template for create/edit/clone
    return render_template("estimates/new_standard.html", estimate=est, mode="edit")

@bp.get("/<int:estimate_id>/clone")
def clone_start(estimate_id: int):
    est = Estimate.query.filter_by(id=estimate_id, org_id=current_user.org_id).first_or_404()
    return render_template("estimates/new_standard.html", estimate=est, mode="clone")

@bp.put("/<int:estimate_id>")
def update(estimate_id: int):
    est = Estimate.query.filter_by(id=estimate_id, org_id=current_user.org_id).first_or_404()
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"errors": {"name": "Name is required"}}), 400

    def _s(key):
        v = (data.get(key) or "").strip()
        return v or None

    customer_id = data.get("customer_id")
    try:
        customer_id = int(customer_id) if str(customer_id or "").isdigit() else None
    except Exception:
        customer_id = None

    est.name = name
    est.project_address = _s("project_address")
    est.project_ref = _s("project_ref")
    est.customer_id = customer_id

    db.session.commit()
    return jsonify({"ok": True, "id": est.id})

@bp.get("/<int:estimate_id>.json")
def get_estimate_json(estimate_id: int):
    e = Estimate.query.filter_by(id=estimate_id, org_id=current_user.org_id).first_or_404()
    return jsonify({
        "id": e.id,
        "name": e.name,
        "customer_id": e.customer_id,
        "project_address": e.project_address or "",
        "project_ref": e.project_ref or "",
        "status": e.status,
        "settings_snapshot": e.settings_snapshot or {},
        "created_at": e.created_at.isoformat() if e.created_at else None,
        "updated_at": e.updated_at.isoformat() if e.updated_at else None,
    })

@bp.put("/<int:estimate_id>/payload")
def save_payload(estimate_id: int):
    est = Estimate.query.filter_by(id=estimate_id, org_id=current_user.org_id).first_or_404()
    data = request.get_json(silent=True) or {}
    # NOTE: full tenant scoping lands in 03b.8; for now, auth is enforced by blueprint guard
    est.work_payload = data
    db.session.commit()
    return jsonify(ok=True, id=est.id)

@bp.get("/<int:estimate_id>/payload.json")
def get_payload_json(estimate_id: int):
    est = Estimate.query.filter_by(id=estimate_id, org_id=current_user.org_id).first_or_404()
    return jsonify(ok=True, id=est.id, payload=est.work_payload or {})


@bp.post("/<int:estimate_id>/clone")
def clone_estimate(estimate_id: int):
    e =Estimate.query.filter_by(id=estimate_id, org_id=current_user.org_id).first_or_404()
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
    e = Estimate.query.filter_by(id=estimate_id, org_id=current_user.org_id).first_or_404()
    db.session.delete(e)
    db.session.commit()
    return ("", 204)

@bp.get("/fast")
def fast():
    return render_template("estimates/fast.html")  # stub for later

@bp.get("/<int:estimate_id>")
def view(estimate_id):
    return render_template("estimates/view.html", estimate_id=estimate_id)  # stub for later

@bp.get("/recent.json")
def recent_json():
    rows = (
        db.session.query(Estimate, Customer.company_name)
        .outerjoin(Customer, Estimate.customer_id == Customer.id)
        .filter(Estimate.org_id == current_user.org_id)
        .order_by(Estimate.updated_at.desc())
        .limit(3)
        .all()
    )
    data = [
        {
            "id": e.id,
            "name": e.name,
            "customer_id": e.customer_id,
            "customer_name": cname,
            "status": e.status,
            "updated_at": e.updated_at.isoformat() if e.updated_at else None,
        }
        for (e, cname) in rows
    ]
    return jsonify(ok=True, rows=data)
