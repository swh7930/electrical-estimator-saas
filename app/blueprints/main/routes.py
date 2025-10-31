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
    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = request.form or {}

    message = (data.get("message") or "").strip()
    if not message:
        if "application/json" in (request.headers.get("Accept") or ""):
            return jsonify({"ok": False, "error": "Message is required"}), 400
        flash("Please enter a message.", "warning")
        return redirect(url_for("main.feedback_get"))

    raw_path = (data.get("path") or request.headers.get("Referer") or "/").strip()
    try:
        u = urlparse(raw_path)
        path = (u.path or "/") + (f"?{u.query}" if u.query else "")
    except Exception:
        path = "/"
    path = path[:255]  # DB column max

    uid = None
    oid = None
    try:
        if getattr(current_user, "is_authenticated", False):
            uid = getattr(current_user, "id", None)
            oid = session.get("current_org_id") or getattr(current_user, "org_id", None)
    except Exception:
        pass

    fb = Feedback(user_id=uid, org_id=oid, path=path, message=message)
    db.session.add(fb)
    db.session.commit()

    # Structured JSON log (no message content for privacy)
    try:
        current_app.logger.info(
            "feedback_submitted",
            extra={"event": "feedback_submitted", "user_id": uid, "org_id": oid, "path": path},
        )
    except Exception:
        pass

    if "application/json" in (request.headers.get("Accept") or ""):
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
