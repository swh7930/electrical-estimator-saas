from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import current_user
from flask import session
from urllib.parse import urlparse
from app.extensions import db
from app.models.feedback import Feedback
from . import bp

@bp.get("/")
def home():
    return render_template("home.html")

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



# --- TEMPORARY PREVIEW ROUTES (visual only) ---

@bp.get("/home-cards")
def home_cards():
    return render_template("home_alt_cards.html")

@bp.get("/home-sidebar")
def home_sidebar():
    return render_template("home_alt_sidebar.html")
