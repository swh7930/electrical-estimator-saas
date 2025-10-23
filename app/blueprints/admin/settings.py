from flask import render_template, request, jsonify, session
from sqlalchemy.sql import func
from . import bp
from flask_login import current_user

from app.extensions import db
from app.models.app_settings import AppSettings
from app.services.policy import require_member, role_required
from app.models.org_membership import OrgMembership,  ROLE_ADMIN, ROLE_OWNER

@bp.get("/settings")
def settings():
    def _can_write_settings():
        if not current_user.is_authenticated:
            return False
        org_id = session.get("current_org_id") or getattr(current_user, "org_id", None)
        if not org_id:
            return False
        m = db.session.query(OrgMembership).filter_by(org_id=org_id, user_id=current_user.id).one_or_none()
        return bool(m and m.role in (ROLE_ADMIN, ROLE_OWNER))

    return render_template("admin/settings.html", settings=settings, can_write=_can_write_settings())


@bp.get("/settings.json")
@require_member
def get_settings_json():
    row = db.session.execute(
        db.select(AppSettings).where(AppSettings.org_id == current_user.org_id)
    ).scalar_one_or_none()

    if not row:
        # Keep your existing semantics: return {} when no settings exist yet
        return jsonify({})

    return jsonify(row.to_dict())

@bp.put("/settings.json")
@role_required(ROLE_ADMIN, ROLE_OWNER)
def put_settings_json():
    payload = request.get_json(silent=True) or {}
    incoming = payload.get("settings", {})

    if not isinstance(incoming, dict):
        return jsonify({"error": "Invalid payload"}), 400

    # Minimal shape coercion (numbers >= 0 where expected)
    p = incoming.get("pricing", {}) or {}
    def _int(name, default=None, lo=0, hi=1000):
        try:
            v = int(p.get(name)) if p.get(name) is not None else default
            if v is None:
                return None
            return max(lo, min(hi, v))
        except Exception:
            return default

    coerced = {
        "org": {
            "company_name": (incoming.get("org", {}) or {}).get("company_name") or "",
            "legal_name": (incoming.get("org", {}) or {}).get("legal_name") or "",
            "contact_name": (incoming.get("org", {}) or {}).get("contact_name") or "",
            "email":       (incoming.get("org", {}) or {}).get("email") or "",
            "phone":       (incoming.get("org", {}) or {}).get("phone") or "",
            "website":     (incoming.get("org", {}) or {}).get("website") or "",
            "address1":    (incoming.get("org", {}) or {}).get("address1") or "",
            "address2":    (incoming.get("org", {}) or {}).get("address2") or "",
            "city":        (incoming.get("org", {}) or {}).get("city") or "",
            "state":       (incoming.get("org", {}) or {}).get("state") or "",
            "zip":         (incoming.get("org", {}) or {}).get("zip") or "",
            "license_no":  (incoming.get("org", {}) or {}).get("license_no") or "",
            "proposal_footer": (incoming.get("org", {}) or {}).get("proposal_footer") or "",
        },
        "pricing": {
            "labor_rate": float(p.get("labor_rate") or 0) if str(p.get("labor_rate") or "").strip() else 0.0,
            "overhead_percent": _int("overhead_percent", 30, 0, 100),
            "margin_percent":   _int("margin_percent", 10, 0, 100),
            "sales_tax_percent": _int("sales_tax_percent", 8, 0, 100),
            "misc_percent":        _int("misc_percent", 10, 0, 100),
            "small_tools_percent": _int("small_tools_percent", 5, 0, 100),
            "large_tools_percent": _int("large_tools_percent", 3, 0, 100),
            "waste_theft_percent": _int("waste_theft_percent", 10, 0, 100),
        },
        "version": int(incoming.get("version") or 1),
    }

    row = db.session.execute(
        db.select(AppSettings).where(AppSettings.org_id == current_user.org_id)
    ).scalar_one_or_none()

    if not row:
        row = AppSettings(org_id=current_user.org_id, settings=coerced, settings_version=1)
        db.session.add(row)
    else:
        row.settings = coerced
        row.settings_version = (row.settings_version or 1) + 1

        # keep updated_at fresh
        row.updated_at = func.now()
        db.session.commit()

    return jsonify(row.to_dict())
