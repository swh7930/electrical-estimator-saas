from flask import render_template, request, jsonify, redirect, url_for
from . import bp
from app.extensions import db
from app.models.estimate import Estimate
from app.models.app_settings import AppSettings

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


@bp.get("/fast")
def fast():
    return render_template("estimates/fast.html")  # stub for later

@bp.get("/<int:estimate_id>")
def view(estimate_id):
    return render_template("estimates/view.html", estimate_id=estimate_id)  # stub for later
