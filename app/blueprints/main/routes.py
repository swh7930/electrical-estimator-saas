from flask import render_template, request, redirect, url_for, flash, jsonify, current_app, abort
from flask_login import current_user, login_required
from flask import session
from urllib.parse import urlparse
import os

from app.extensions import db
from app.models import Subscription
from app.models.feedback import Feedback
from . import bp

@bp.get("/")
def home():
    show_settings_nudge = bool(session.pop("post_checkout_nudge", False))
    return render_template("home.html", show_settings_nudge=show_settings_nudge)

@bp.get("/pricing")
def pricing():
    """Public pricing page (state-aware CTAs; no inline JS)."""
    # Determine active subscription for current org (mirrors billing/index logic)
    is_active = False
    try:
        if getattr(current_user, "is_authenticated", False):
            org_id = getattr(current_user, "org_id", None) or session.get("current_org_id")
            if org_id:
                s = Subscription.query.filter_by(org_id=org_id).first()
                is_active = bool(s and (s.status in {"active","trialing"}))
    except Exception:
        is_active = False

    cfg = current_app.config
    ctx = {
        "is_active": is_active,
        "price_pro_monthly": cfg.get("STRIPE_PRICE_PRO_MONTHLY"),
        "price_pro_annual": cfg.get("STRIPE_PRICE_PRO_ANNUAL"),
        "price_elite_monthly": cfg.get("STRIPE_PRICE_ELITE_MONTHLY"),
        "price_elite_annual": cfg.get("STRIPE_PRICE_ELITE_ANNUAL"),
    }
    return render_template("pricing.html", **ctx)

@bp.get("/feedback")
def feedback_get():
    """Fallback page for no-JS users."""
    ref = request.args.get("path") or (request.referrer or "/")
    try:
        u = urlparse(ref)
        from_path = (u.path or "/") + (f"?{u.query}" if u.query else "")
    except Exception:
        from_path = "/"
    return render_template("feedback.html", from_path=from_path)

@bp.post("/feedback")
def feedback_post():
    """Accept feedback from modal (JSON) or fallback form (HTML)."""
    accepts = (request.headers.get("Accept") or "")
    wants_json = ("application/json" in accepts) or request.is_json

    data = (request.get_json(silent=True) or {}) if request.is_json else (request.form or {})

    message = (data.get("message") or "").strip()
    # Debug (non-PII): help confirm what the server received without logging the message
    try:
        current_app.logger.info(
            "feedback_debug",
            extra={
                "event": "feedback_debug",
                "is_json": bool(request.is_json),
                "accept": accepts,
                "keys": list(data.keys()),
                "message_len": len(message),
            },
        )
    except Exception:
        pass

    if not message:
        if wants_json:
            return jsonify({"ok": False, "error": "Message is required"}), 400
        flash("Please enter a message.", "warning")
        return redirect(url_for("main.feedback_get"))

    raw_path = (data.get("path") or request.headers.get("Referer") or "/").strip()
    try:
        u = urlparse(raw_path)
        path = (u.path or "/") + (f"?{u.query}" if u.query else "")
    except Exception:
        path = "/"
    path = path[:255]

    uid = getattr(current_user, "id", None) if getattr(current_user, "is_authenticated", False) else None
    oid = session.get("current_org_id") or getattr(current_user, "org_id", None) if getattr(current_user, "is_authenticated", False) else None

    fb = Feedback(user_id=uid, org_id=oid, path=path, message=message)
    db.session.add(fb)
    db.session.commit()

    # Structured log for observability (no message body to avoid PII)
    try:
        current_app.logger.info(
            "feedback_submitted",
            extra={"event": "feedback_submitted", "user_id": uid, "org_id": oid, "path": path},
        )
    except Exception:
        pass

    if wants_json:
        return jsonify({"ok": True})
    flash("Thanks for your feedback!", "success")
    return redirect(path or url_for("main.home"))

@bp.get("/admin/feedback")
@login_required
def admin_feedback_index():
    """App OWNER only (env allow-list). Org/account owners are NOT allowed."""
    owner_csv = (os.getenv("EESAAS_OWNER_EMAILS") or "").strip()
    if not owner_csv:
        abort(403)  # explicit: if owner list isn't set, nobody gets in

    allowed = {e.strip().lower() for e in owner_csv.split(",") if e.strip()}
    cur_email = (getattr(current_user, "email", "") or getattr(current_user, "username", "") or "").lower()

    if cur_email not in allowed:
        abort(403)

    items = Feedback.query.order_by(Feedback.created_at.desc()).all()
    return render_template("admin/feedback_index.html", items=items)

