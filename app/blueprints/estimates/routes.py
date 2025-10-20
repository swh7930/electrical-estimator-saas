from flask import render_template, request, jsonify, redirect, url_for
from flask import make_response
import csv, io
from decimal import Decimal, ROUND_HALF_UP
from app.models.material import Material
from app.models.dje_item import DjeItem
from app.services.assemblies import get_assembly_rollup, ServiceError
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

@bp.get("/<int:estimate_id>/export/summary.csv")
def export_summary_csv(estimate_id: int):
    # Scope: tenant-owned estimate only
    est = Estimate.query.filter_by(id=estimate_id, org_id=current_user.org_id).first_or_404()
    payload = est.work_payload or {}
    grid = (payload.get("grid") or {}).get("rows") or []
    totals = payload.get("totals") or {}
    estdata = payload.get("estimateData") or {}
    dje_costs = (estdata.get("costs") or {})
    dje_rows = dje_costs.get("dje_rows") or []

    # CSV buffer
    buf = io.StringIO(newline="")
    w = csv.writer(buf)

    # Header (fixed order)
    header = [
        "line_no","section","material_type","category","subcategory","description","notes",
        "qty","unit","labor_adj","cost_ea","material_ext","labor_unit","labor_hrs"
    ]
    w.writerow(header)

    # Helpers
    q2 = lambda d: f"{(Decimal(d) if d is not None else Decimal('0')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}"
    q4 = lambda d: f"{(Decimal(d) if d is not None else Decimal('0')).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)}"
    to_dec = lambda v: (Decimal(str(v)) if v not in (None, "") else Decimal("0"))

    line_no = 1

    # ---- MATERIAL / ASSEMBLY lines from estimator grid ----
    for row in grid:
        try:
            rtype = (row.get("type") or "").strip()
            desc_text = (row.get("descText") or "").strip()
            desc_val = row.get("descValue")
            qty = to_dec(row.get("qty"))
            ladj = to_dec(row.get("ladj") or "1")
            unit = "1"  # UI normalizes to per-each in estimator

            # Default fields
            section = "MATERIAL"
            mat_type = rtype
            category = ""
            subcategory = ""
            cost_ea = Decimal("0")
            labor_unit = Decimal("0")

            # Assemblies (when Type == 'Assemblies')
            if rtype == "Assemblies" and desc_val:
                try:
                    info = get_assembly_rollup(int(desc_val), org_id=current_user.org_id)
                    # Per single assembly
                    cost_ea = to_dec(info.get("material_cost_total"))
                    labor_unit = to_dec(info.get("labor_hours_total"))
                    section = "ASSEMBLY"
                except ServiceError:
                    # Not found or cross-tenant → treat as zeroed line (still exportable)
                    cost_ea = Decimal("0")
                    labor_unit = Decimal("0")

            # Materials (default)
            elif desc_val:
                mat = (
                    db.session.query(Material)
                    .filter(Material.id == int(desc_val))
                    .filter(Material.org_id == current_user.org_id)
                    .one_or_none()
                )
                if mat:
                    # API/UI use price and labor_unit as per-each values
                    cost_ea = to_dec(mat.price)
                    labor_unit = to_dec(mat.labor_unit)
                # else: leave zeros (stale ref / cross-tenant)

            # Compute extensions
            material_ext = (qty * cost_ea).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            labor_hrs = (qty * labor_unit * ladj).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

            w.writerow([
                line_no, section, mat_type, category, subcategory, desc_text, (row.get("notes") or ""),
                f"{qty.normalize()}", unit, f"{ladj.normalize()}",
                q2(cost_ea), q2(material_ext), q4(labor_unit), q4(labor_hrs)
            ])
            line_no += 1

        except Exception:
            # Keep export resilient; skip malformed rows
            continue

    # ---- DJE lines from DJE page ----
    for drow in dje_rows:
        try:
            desc_id = drow.get("desc_id")
            qty = to_dec(drow.get("qty"))
            multi = to_dec(drow.get("multi") or "1")
            notes = drow.get("notes") or ""
            category = ""
            subcategory = ""
            desc_text = ""

            cost_ea = Decimal("0")
            labor_unit = Decimal("0")  # DJE has no labor unit
            labor_hrs = Decimal("0")

            if desc_id:
                item = (
                    db.session.query(DjeItem)
                    .filter(DjeItem.id == int(desc_id))
                    .filter(DjeItem.org_id == current_user.org_id)
                    .one_or_none()
                )
                if item:
                    category = item.category or ""
                    subcategory = item.subcategory or ""
                    # description field name is 'description' on DJE items
                    desc_text = item.description or ""
                    cost_ea = to_dec(item.default_unit_cost)

            material_ext = (qty * multi * cost_ea).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            w.writerow([
                line_no, "DJE", "", category, subcategory, desc_text, notes,
                f"{qty.normalize()}", "", "1",
                q2(cost_ea), q2(material_ext), q4(labor_unit), q4(labor_hrs)
            ])
            line_no += 1

        except Exception:
            continue

    # ---- Totals rows (end) ----
    mat_total = to_dec(totals.get("material_cost_price_sheet"))
    labor_total = to_dec(totals.get("labor_hours_pricing_sheet"))

    w.writerow([line_no, "TOTALS", "", "", "", "Material Total", "", "", "", "", "", q2(mat_total), "", ""])
    line_no += 1
    w.writerow([line_no, "TOTALS", "", "", "", "Labor Hours Total", "", "", "", "", "", "", "", q4(labor_total)])

    # Build response
    csv_str = buf.getvalue()
    buf.close()
    stamp = datetime.now().strftime("%Y%m%d")
    filename = f"estimate_{estimate_id}_summary_{stamp}.csv"

    resp = make_response(csv_str)
    resp.headers["Content-Type"] = "text/csv; charset=utf-8"
    resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp

@bp.get("/export/index.csv")
def export_estimates_index_csv():
    # Org-scoped list of estimates; optional query-string filters may be appended by the UI.
    q = (request.args.get("q") or "").strip()

    # Base query (tenant isolation)
    rows = (
        db.session.query(Estimate, Customer)
        .outerjoin(Customer, Estimate.customer_id == Customer.id)
        .filter(Estimate.org_id == current_user.org_id)
        .order_by(Estimate.created_at.desc())
        .all()
    )

    # Simple 'q' filter if present (matches name/title and customer company, case-insensitive)
    if q:
        q_lc = q.lower()
        rows = [
            (est, cust)
            for (est, cust) in rows
            if (
                (getattr(est, "name", "") or getattr(est, "title", "") or "").lower().find(q_lc) != -1
                or ((cust.company_name if cust else "") or "").lower().find(q_lc) != -1
            )
        ]

    # CSV buffer
    buf = io.StringIO(newline="")
    w = csv.writer(buf)

    # Header
    header = [
        "id","name","customer","status","created_at","updated_at","material_total","labor_hours_total"
    ]
    w.writerow(header)

    q2 = lambda d: f"{(Decimal(d) if d is not None else Decimal('0')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}"
    q4 = lambda d: f"{(Decimal(d) if d is not None else Decimal('0')).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)}"
    to_dec = lambda v: (Decimal(str(v)) if v not in (None, "") else Decimal("0"))

    for est, cust in rows:
        payload = est.work_payload or {}
        totals = payload.get("totals") or {}

        mat_total = to_dec(totals.get("material_cost_price_sheet"))
        labor_total = to_dec(totals.get("labor_hours_pricing_sheet"))

        name = (getattr(est, "name", None) or getattr(est, "title", None) or "").strip()
        customer = (cust.company_name if cust else "") or ""
        # Graceful status fallback (string if available; else active/inactive)
        status = getattr(est, "status", None)
        if status is None:
            status = "active" if getattr(est, "is_active", True) else "inactive"

        created = est.created_at.strftime("%Y-%m-%d %H:%M:%S") if getattr(est, "created_at", None) else ""
        updated = est.updated_at.strftime("%Y-%m-%d %H:%M:%S") if getattr(est, "updated_at", None) else ""

        w.writerow([
            est.id, name, customer, status, created, updated, q2(mat_total), q4(labor_total)
        ])

    csv_str = buf.getvalue()
    buf.close()

    stamp = datetime.now().strftime("%Y%m%d")
    filename = f"estimates_index_{stamp}.csv"

    resp = make_response(csv_str)
    resp.headers["Content-Type"] = "text/csv; charset=utf-8"
    resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp



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
