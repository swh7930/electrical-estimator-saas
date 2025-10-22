from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app, make_response, send_file, abort
import csv, io, os
from decimal import Decimal, ROUND_HALF_UP
from app.models.material import Material
from app.models.dje_item import DjeItem
from app.models.assembly import Assembly
from app.services.assemblies import get_assembly_rollup, ServiceError
from sqlalchemy import func, or_
from datetime import datetime
from . import bp
from .validators import validate_fast_export_payload
from flask_login import login_required, current_user
from app.extensions import db
from app.models.estimate import Estimate
from app.models.app_settings import AppSettings
from app.models.customer import Customer
from weasyprint import HTML, CSS
from io import BytesIO

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
    """
    Saved Export (CSV)
    Source of truth: saved payload snapshot (summary_export.controls + summary_export.cells).
    No calculations here.
    """
    est = Estimate.query.filter_by(id=estimate_id, org_id=current_user.org_id).first_or_404()
    payload = est.work_payload or {}

    # Resolve snapshot; fall back to full payload to stay graceful
    summary = (
        (payload.get("estimateData") or {}).get("summary_export")
        or payload.get("summary_export")
        or payload.get("summary_totals")
        or payload.get("summary")
        or payload.get("summary_snapshot")
        or payload
    )

    def _get_controls(s):
        try:
            se = s.get("summary_export") if isinstance(s.get("summary_export"), dict) else s.get("summaryExport")
            if isinstance(se, dict) and isinstance(se.get("controls"), dict):
                return se["controls"]
            if isinstance(s.get("controls"), dict):
                return s["controls"]
        except Exception:
            pass
        return None

    def _get_cells(s):
        try:
            se = s.get("summary_export") if isinstance(s.get("summary_export"), dict) else s.get("summaryExport")
            if isinstance(se, dict) and isinstance(se.get("cells"), dict):
                return se["cells"]
            if isinstance(s.get("cells"), dict):
                return s["cells"]
        except Exception:
            pass
        return None

    controls = _get_controls(summary)
    cells    = _get_cells(summary)
    totals   = summary.get("totals") if isinstance(summary, dict) and isinstance(summary.get("totals"), dict) else None

    buf = io.StringIO(newline="")
    w = csv.writer(buf)
    w.writerow(["section", "key", "value"])

    # Controls first (fixed order; only write keys that exist)
    order_controls = [
        "labor_rate",
        "margin_percent",
        "overhead_percent",
        "misc_percent",
        "small_tools_percent",
        "large_tools_percent",
        "waste_theft_percent",
        "sales_tax_percent",
    ]
    if isinstance(controls, dict) and controls:
        for k in order_controls:
            if k in controls:
                w.writerow(["controls", k, controls[k]])
        for k, v in controls.items():
            if k not in order_controls:
                w.writerow(["controls", k, v])

    # Cells next by your exact DOM ids (exclude form inputs/selects)
    id_order = [
        "labor-hours-pricing-sheet",
        "summaryAdjustedHours",
        "summaryAdditionalHours",
        "summaryTotalHours",
        "summaryTotalLaborCost",
        "material-cost-price-sheet",
        "miscMaterialValue",
        "smallToolsValue",
        "largeToolsValue",
        "wasteTheftValue",
        "taxableMaterialValue",
        "salesTaxValue",
        "totalMaterialCostValue",
        "djeValue",
        "primeCostValue",
        "overheadValue",
        "breakEvenValue",
        "markupValue",
        "profitMarginValue",
        "estimatedSalesPriceValue",
        "oneManDays",
        "twoManDays",
        "fourManDays",
    ]
    if isinstance(cells, dict) and cells:
        for cid in id_order:
            if cid in cells:
                w.writerow(["cells", cid, cells[cid]])
        for cid, val in cells.items():
            if cid not in id_order:
                w.writerow(["cells", cid, val])

    # If there were no cells but you have a totals dict, include it last
    if (not cells) and isinstance(totals, dict) and totals:
        for k, v in totals.items():
            w.writerow(["totals", k, v])

    csv_str = buf.getvalue()
    buf.close()

    stamp = datetime.utcnow().strftime("%Y%m%d")
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

@bp.get("/<int:estimate_id>/export/summary.pdf")
def export_summary_pdf(estimate_id: int):
    """
    HF1: Saved Export (PDF)
    - No route math.
    - Load saved snapshot-like summary only.
    - If missing, return 409 JSON.
    - Temporary minimal PDF content; HF2 will render the real Summary clone.
    """
    est = Estimate.query.filter_by(id=estimate_id, org_id=current_user.org_id).first_or_404()
    payload = est.work_payload or {}

    summary = ((payload.get("estimateData") or {}).get("summary_export")
           or payload.get("summary_totals")
           or payload.get("summary")
           or payload.get("summary_snapshot"))

    # HF2a: gracefully fall back to full payload so Saved Export still works.
    # No math here — the Jinja template renders defensively for now.
    if not summary:
        summary = payload

    # Render via Jinja template (structural step)
    html = render_template(
        "exports/summary_pdf.html",
        estimate=est,
        summary=summary,   # saved snapshot we already located
        mode="SAVED"
    )

    site_css = os.path.join(current_app.root_path, "static", "css", "site.css")
    pdf_css  = os.path.join(current_app.root_path, "static", "css", "pdf.css")
    pdf_bytes = HTML(string=html, base_url=request.host_url).write_pdf(
        stylesheets=[CSS(filename=site_css), CSS(filename=pdf_css)]
    )

    stamp = datetime.utcnow().strftime("%Y%m%d")
    filename = f"estimate_{estimate_id}_summary_{stamp}.pdf"
    resp = make_response(pdf_bytes)
    resp.headers["Content-Type"] = "application/pdf"
    resp.headers["Content-Disposition"] = f'inline; filename="{filename}"'
    return resp

@bp.post("/exports/summary.csv")
def fast_export_summary_csv():
    """
    Fast Export (CSV)
    Accepts payload with summary_export.controls and/or summary_export.cells.
    No calculations here.
    """
    data = request.get_json(silent=True) or {}
    errors = validate_fast_export_payload(data)
    if errors:
        return jsonify({"error": "invalid_payload", "fields": errors}), 422

    def _get_controls(s):
        try:
            se = s.get("summary_export") if isinstance(s.get("summary_export"), dict) else s.get("summaryExport")
            if isinstance(se, dict) and isinstance(se.get("controls"), dict):
                return se["controls"]
            if isinstance(s.get("controls"), dict):
                return s["controls"]
        except Exception:
            pass
        return None

    def _get_cells(s):
        try:
            se = s.get("summary_export") if isinstance(s.get("summary_export"), dict) else s.get("summaryExport")
            if isinstance(se, dict) and isinstance(se.get("cells"), dict):
                return se["cells"]
            if isinstance(s.get("cells"), dict):
                return s["cells"]
        except Exception:
            pass
        return None

    controls = _get_controls(data)
    cells    = _get_cells(data)
    totals   = data.get("totals") if isinstance(data, dict) and isinstance(data.get("totals"), dict) else None

    buf = io.StringIO(newline="")
    w = csv.writer(buf)
    w.writerow(["section", "key", "value"])

    order_controls = [
        "labor_rate",
        "margin_percent",
        "overhead_percent",
        "misc_percent",
        "small_tools_percent",
        "large_tools_percent",
        "waste_theft_percent",
        "sales_tax_percent",
    ]
    if isinstance(controls, dict) and controls:
        for k in order_controls:
            if k in controls:
                w.writerow(["controls", k, controls[k]])
        for k, v in controls.items():
            if k not in order_controls:
                w.writerow(["controls", k, v])

    id_order = [
        "labor-hours-pricing-sheet",
        "summaryAdjustedHours",
        "summaryAdditionalHours",
        "summaryTotalHours",
        "summaryTotalLaborCost",
        "material-cost-price-sheet",
        "miscMaterialValue",
        "smallToolsValue",
        "largeToolsValue",
        "wasteTheftValue",
        "taxableMaterialValue",
        "salesTaxValue",
        "totalMaterialCostValue",
        "djeValue",
        "primeCostValue",
        "overheadValue",
        "breakEvenValue",
        "markupValue",
        "profitMarginValue",
        "estimatedSalesPriceValue",
        "oneManDays",
        "twoManDays",
        "fourManDays",
    ]
    if isinstance(cells, dict) and cells:
        for cid in id_order:
            if cid in cells:
                w.writerow(["cells", cid, cells[cid]])
        for cid, val in cells.items():
            if cid not in id_order:
                w.writerow(["cells", cid, val])

    if (not cells) and isinstance(totals, dict) and totals:
        for k, v in totals.items():
            w.writerow(["totals", k, v])

    csv_str = buf.getvalue()
    buf.close()

    stamp = datetime.utcnow().strftime("%Y%m%d")
    filename = f"estimate_fast_summary_{stamp}.csv"

    resp = make_response(csv_str)
    resp.headers["Content-Type"] = "text/csv; charset=utf-8"
    resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


@bp.post("/exports/summary.pdf")
def fast_export_summary_pdf():
    """
    HF1: Fast Export (PDF)
    - Accept finalized export payload from the UI (unsaved fast mode).
    - Validate minimal shape; do not perform any math.
    - Temporary minimal PDF content; HF2 will render the real Summary clone.
    """
    data = request.get_json(silent=True) or {}
    errors = validate_fast_export_payload(data)
    if errors:
        return jsonify({"error": "invalid_payload", "fields": errors}), 422

    # Render via Jinja template (structural step)
    html = render_template(
        "exports/summary_pdf.html",
        estimate=None,     # not saved; no Estimate record
        summary=data,      # validated fast payload
        mode="FAST"
    )

    site_css = os.path.join(current_app.root_path, "static", "css", "site.css")
    pdf_css  = os.path.join(current_app.root_path, "static", "css", "pdf.css")
    pdf_bytes = HTML(string=html, base_url=request.host_url).write_pdf(
        stylesheets=[CSS(filename=site_css), CSS(filename=pdf_css)]
    )

    stamp = datetime.utcnow().strftime("%Y%m%d")
    filename = f"estimate_fast_summary_{stamp}.pdf"
    resp = make_response(pdf_bytes)
    resp.headers["Content-Type"] = "application/pdf"
    resp.headers["Content-Disposition"] = f'inline; filename="{filename}"'
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
