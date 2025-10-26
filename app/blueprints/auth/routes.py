from flask import render_template, request, redirect, url_for, session, jsonify
from flask_login import login_user, logout_user, current_user
from sqlalchemy import func
from app.extensions import db, limiter
from app.models.user import User
from app.models.org import Org
from app.models.org_membership import OrgMembership, ROLE_OWNER, ROLE_MEMBER
from . import bp
from app.services import tokens
from app.services.email import send_verification_email, send_password_reset_email
from flask_wtf.csrf import generate_csrf
from app.extensions import csrf


def _login_email_scope():
    data_json = request.get_json(silent=True) or {}
    email = (request.form.get("email") or data_json.get("email") or "").strip().lower()
    # Keep a stable scope even if email is blank
    return f"login-email:{email or 'missing'}"

@bp.get("/login")
def login_get():
    if current_user.is_authenticated:
        next_url = request.args.get("next") or url_for("main.home")
        return redirect(next_url)
    return render_template("auth/login.html")

@bp.post("/login")
@limiter.limit("10 per minute; 100 per hour")              # per-IP (anon → IP via _rate_limit_key)
@limiter.limit("5 per minute; 20 per hour", key_func=_login_email_scope)  # per-account
def login_post():
    email = (request.form.get("email") or "").strip()
    password = request.form.get("password") or ""

    if not email or not password:
        return render_template("auth/login.html", error="Email and password are required"), 400

    user = db.session.execute(
        db.select(User).where(func.lower(User.email) == func.lower(email))
    ).scalar_one_or_none()

    if not user or not user.check_password(password) or not user.is_active:
        return render_template("auth/login.html", error="Invalid credentials"), 400

    # Guarantee the user has an org (tenant) before we start a session
    if not user.org_id:
        # create a simple org label; you can rename later in an account screen
        org = Org(name=(user.email or f"Org {user.id}"))
        db.session.add(org); db.session.flush()
        user.org_id = org.id
        db.session.commit()

    # --- S3-03b.3a: ensure org membership + set current_org_id ---
    # Assumptions (per clean-slate prod): users & org created above if brand-new.
    org_id = user.org_id

    if org_id is not None:
        # Create membership if missing.
        membership = db.session.query(OrgMembership).filter_by(org_id=org_id, user_id=user.id).one_or_none()
        if membership is None:
            # Owner if no owners exist yet in this org, otherwise member.
            owner_exists = db.session.query(OrgMembership).filter_by(org_id=org_id, role=ROLE_OWNER).count() > 0
            role = ROLE_MEMBER if owner_exists else ROLE_OWNER
            membership = OrgMembership(org_id=org_id, user_id=user.id, role=role)
            db.session.add(membership)
            db.session.commit()

        # Stash org context in the session (policy will prefer path/resource, fall back to this).
        session["current_org_id"] = org_id
    # --- /S3-03b.3a ---

    login_user(user)
    next_url = request.args.get("next") or url_for("main.home")
    return redirect(next_url)

@bp.get("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for("main.home"))

@bp.post("/logout")
def logout_post():
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for("main.home"))

@bp.post("/verify/resend")
@limiter.limit("3 per hour")
def resend_verification():
    if not current_user.is_authenticated:
        # Normalize: same behavior whether logged-in or not
        return redirect(url_for("auth.login_get"))
    # If already verified, do nothing but return OK-ish
    if getattr(current_user, "email_verified_at", None):
        return redirect(url_for("main.home"))
    send_verification_email(current_user)
    return redirect(url_for("main.home"))

@bp.get("/verify")
def verify_email():
    token = (request.args.get("token") or "").strip()
    if not token:
        return redirect(url_for("auth.login_get", verified="0"))

    # TTL must match email service default: 30 minutes
    email = tokens.verify("verify", token, max_age_seconds=30 * 60)
    if not email:
        return redirect(url_for("auth.login_get", verified="0"))

    user = User.query.filter(func.lower(User.email) == email.lower()).first()
    if not user:
        return redirect(url_for("auth.login_get", verified="0"))

    if not getattr(user, "email_verified_at", None):
        user.email_verified_at = func.now()
        db.session.commit()

    return redirect(url_for("auth.login_get", verified="1"))

@bp.post("/password/reset-request")
@limiter.limit("10 per hour")
def reset_request():
    data = request.get_json(silent=True) or request.form
    email = (data.get("email") or "").strip().lower()
    if email:
        user = User.query.filter(func.lower(User.email) == email).first()
        if user:
            send_password_reset_email(user)  # TTL default is 120 minutes in email.py
    # Always respond the same way
    return redirect(url_for("auth.login_get"))

@bp.get("/register")
def register_get():
    if current_user.is_authenticated:
        next_url = request.args.get("next") or url_for("main.home")
        return redirect(next_url)
    return render_template("auth/register.html")

@bp.post("/register")
@limiter.limit("5 per minute; 20 per hour")
def register_post():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    agree = request.form.get("agree") == "on"

    errors = []
    if not email:
        errors.append("Email is required.")
    if not password or len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if not agree:
        errors.append("You must agree to the Terms of Service to continue.")

    # case-insensitive uniqueness check
    existing = None
    if email:
        existing = db.session.execute(
            db.select(User).where(func.lower(User.email) == func.lower(email))
        ).scalar_one_or_none()
    if existing:
        errors.append("An account with that email already exists. Try signing in.")

    if errors:
        return render_template("auth/register.html", errors=errors, email=email), 400

    # Create user + org + membership (owner)
    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()  # get user.id

    org = Org(name=email)  # simple default; user can rename later
    db.session.add(org)
    db.session.flush()

    user.org_id = org.id
    membership = OrgMembership(org_id=org.id, user_id=user.id, role=ROLE_OWNER)
    db.session.add(membership)
    db.session.commit()

    # set org context and log in
    session["current_org_id"] = org.id
    login_user(user)

    return redirect(url_for("billing.index"))

@csrf.exempt
@bp.get("/csrf-token")
def csrf_token():
    token = generate_csrf()
    resp = jsonify({"csrf_token": token})
    # keep tokens fresh; avoid caches holding stale tokens
    resp.headers["Cache-Control"] = "no-store"
    # optional helper cookie; header alone is sufficient for Flask-WTF
    resp.set_cookie("csrf_token", token, samesite="Lax")
    return resp