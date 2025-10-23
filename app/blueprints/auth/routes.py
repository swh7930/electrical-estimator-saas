from flask import render_template, request, redirect, url_for, session
from flask_login import login_user, logout_user, current_user
from sqlalchemy import func
from app.extensions import db, limiter
from app.models.user import User
from app.models.org import Org
from app.models.org_membership import OrgMembership, ROLE_OWNER, ROLE_MEMBER
from . import bp

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

