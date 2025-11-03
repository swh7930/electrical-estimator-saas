from flask import render_template, request, redirect, url_for, session, jsonify, flash, current_app
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

# Only allow internal paths like "/estimates" (no external URLs or "//" protocol-relative).
def _safe_next_path(next_raw: str) -> str:
    next_raw = (next_raw or "").strip()
    if next_raw.startswith("/") and not next_raw.startswith("//"):
        return next_raw
    return url_for("main.home")
@bp.get("/login")
def login_get():
    if current_user.is_authenticated:
        next_raw = request.args.get("next")
        return redirect(_safe_next_path(next_raw))
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
    next_raw = request.args.get("next")
    return redirect(_safe_next_path(next_raw))

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
        next_raw = request.args.get("next")
        return redirect(_safe_next_path(next_raw))
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

# --- Stripe guest handoff: Set Password flow ---

@bp.get("/set-password-start")
def set_password_start():
    """
    Entry from Stripe checkout success (guest or signed-in).
    Create-on-password: do not insert a user yet; issue a short-lived token
    carrying the purchaser's email (and session id if available).
    """
    email = (request.args.get("email") or "").strip().lower()
    if not email:
        return redirect(url_for("auth.login_get"))

    session_id = (request.args.get("session_id") or "").strip()
    payload = {"email": email}
    sid = (request.args.get("session_id") or "").strip()
    if sid: payload["sid"] = sid
    if session_id:
        payload["sid"] = session_id  # optional context

    token = tokens.generate("setpw", payload)  # 60-min TTL enforced in verify()
    return redirect(url_for("auth.set_password", token=token))

@bp.get("/set-password")
def set_password():
    token = (request.args.get("token") or "").strip()
    data = tokens.verify("setpw", token, max_age_seconds=3600)
    if not data:
        flash("This link has expired or is invalid.", "error")
        return redirect(url_for("auth.login_get"))
    return render_template("auth/set_password.html", token=token)

@bp.post("/set-password")
def set_password_post():
    token = (request.form.get("token") or "").strip()
    data = tokens.verify("setpw", token, max_age_seconds=3600)
    if not data:
        flash("This link has expired or is invalid.", "error")
        return redirect(url_for("auth.login_get"))

    password = request.form.get("password") or ""
    confirm = request.form.get("confirm") or ""
    if not password or password != confirm:
        flash("Passwords do not match.", "error")
        return redirect(url_for("auth.set_password", token=token))

    # Resolve or create the user on first set-password after checkout
    user = None
    if isinstance(data, dict) and data.get("uid"):
        # Backward-compatible: token refers to an existing user id
        user = db.session.get(User, data["uid"])
    elif isinstance(data, dict) and data.get("email"):
        email = (data["email"] or "").strip().lower()

        user = db.session.execute(
            db.select(User).where(func.lower(User.email) == func.lower(email))
        ).scalar_one_or_none()

        if not user:
            # New account: create user, set password BEFORE any flush, then org + membership
            user = User(email=email, is_active=True)
            user.set_password(password)      # <-- set hash first (avoids NOT NULL flush)
            db.session.add(user)

            org = Org(name=email)
            db.session.add(org)
            db.session.flush()               # <-- single flush after user has a hash

            user.org_id = org.id
            db.session.add(OrgMembership(org_id=org.id, user_id=user.id, role=ROLE_OWNER))
        else:
            user.is_active = True  # allow Flask-Login to establish the session for an existing account
            # Existing account: make sure org + membership exist
            if not user.org_id:
                org = Org(name=email)
                db.session.add(org)
                db.session.flush()
                user.org_id = org.id
                db.session.add(OrgMembership(org_id=org.id, user_id=user.id, role=ROLE_OWNER))
            else:
                # Ensure membership row exists for the user’s org
                m = db.session.query(OrgMembership).filter_by(
                    org_id=user.org_id, user_id=user.id
                ).one_or_none()
                if not m:
                    db.session.add(OrgMembership(org_id=user.org_id, user_id=user.id, role=ROLE_OWNER))
    else:
        flash("This link has expired or is invalid.", "error")
        return redirect(url_for("auth.login_get"))

    # Finalize account: set password and reconcile subscription (idempotent)
    user.set_password(password)

    # --- BEGIN: Post-checkout Stripe reconcile (attach subscription to org/user) ---
    try:
        # We included 'sid' (Stripe Checkout Session ID) in the token at set_password_start
        sid = data.get("sid")
        if sid:
            # Local imports to avoid touching top-of-file imports
            import stripe
            from datetime import datetime, timezone
            from app.models import BillingCustomer, Subscription
            from app.billing.entitlements import resolve_entitlements

            stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]

            # Get the Checkout Session with expanded subscription
            sess = stripe.checkout.Session.retrieve(sid, expand=["subscription"])
            cust_id = getattr(sess, "customer", None) or (sess.get("customer") if isinstance(sess, dict) else None)
            sub = getattr(sess, "subscription", None) or (sess.get("subscription") if isinstance(sess, dict) else None)

            # Upsert BillingCustomer by stripe_customer_id and attach to org
            if cust_id:
                bc = BillingCustomer.query.filter_by(stripe_customer_id=cust_id).first()
                if not bc:
                    bc = BillingCustomer(
                        org_id=user.org_id,
                        stripe_customer_id=cust_id,
                        billing_email=((getattr(sess, "customer_details", {}) or {}).get("email")
                                       if not isinstance(sess, dict) else (sess.get("customer_details") or {}).get("email")),
                        default_payment_method=None,
                    )
                    db.session.add(bc)
                else:
                    if not getattr(bc, "org_id", None):
                        bc.org_id = user.org_id

            # Upsert Subscription (one per org)
            if sub:
                # Stripe returns a ListObject for sub.items; use its .data (not .get)
                items_obj = getattr(sub, "items", None)
                if items_obj and hasattr(items_obj, "data"):
                    items = items_obj.data or []
                elif isinstance(sub, dict):
                    items = ((sub.get("items") or {}).get("data")) or []
                else:
                    items = []

                first = items[0] if items else None

                # price/product
                if first is not None and hasattr(first, "price"):
                    price = first.price
                elif isinstance(first, dict):
                    price = first.get("price") or {}
                else:
                    price = {}

                price_id = (getattr(price, "id", None)
                            if price and not isinstance(price, dict)
                            else (price.get("id") if isinstance(price, dict) else None))
                product = (getattr(price, "product", None)
                           if price and not isinstance(price, dict)
                           else (price.get("product") if isinstance(price, dict) else None))
                product_id = getattr(product, "id", None) if isinstance(product, dict) else product

                # current_period_end → datetime
                cpe_ts = (getattr(sub, "current_period_end", None)
                          if not isinstance(sub, dict) else sub.get("current_period_end"))
                from_ts = (lambda ts: datetime.fromtimestamp(ts, tz=timezone.utc) if ts else None)
                cpe_dt = from_ts(cpe_ts)

                # quantity
                qty = 1
                if first is not None:
                    qv = (getattr(first, "quantity", None)
                          if not isinstance(first, dict) else first.get("quantity"))
                    try:
                        qty = int(qv) if qv is not None else 1
                    except Exception:
                        qty = 1

                sub_id_val = (getattr(sub, "id", None)
                              if not isinstance(sub, dict) else sub.get("id"))
                sub_status_val = (getattr(sub, "status", None)
                                  if not isinstance(sub, dict) else sub.get("status"))

                s = Subscription.query.filter_by(org_id=user.org_id).first()
                if not s:
                    s = Subscription(
                        org_id=user.org_id,
                        stripe_subscription_id=sub_id_val,
                        product_id=product_id,
                        price_id=price_id,
                        status=sub_status_val or "incomplete",
                        current_period_end=cpe_dt,
                        cancel_at=(getattr(sub, "cancel_at", None)
                                   if not isinstance(sub, dict) else sub.get("cancel_at")),
                        cancel_at_period_end=bool(
                            getattr(sub, "cancel_at_period_end", False)
                            if not isinstance(sub, dict) else sub.get("cancel_at_period_end", False)
                        ),
                        quantity=qty,
                    )
                    db.session.add(s)
                    # initialize entitlements on create
                    s.entitlements_json = resolve_entitlements(product_id=product_id, price_id=price_id)
                else:
                    s.stripe_subscription_id = sub_id_val or s.stripe_subscription_id
                    s.product_id = product_id or s.product_id
                    s.price_id = price_id or s.price_id
                    s.status = (sub_status_val or s.status)
                    s.current_period_end = cpe_dt or s.current_period_end
                    s.cancel_at = (getattr(sub, "cancel_at", None)
                                   if not isinstance(sub, dict) else sub.get("cancel_at"))
                    s.cancel_at_period_end = bool(
                        getattr(sub, "cancel_at_period_end", False)
                        if not isinstance(sub, dict) else sub.get("cancel_at_period_end", False)
                    )
                    s.quantity = qty or s.quantity or 1
                    # backfill entitlements if they were empty from a webhook-first insert
                    if not getattr(s, "entitlements_json", None) and product_id and price_id:
                        s.entitlements_json = resolve_entitlements(product_id=product_id, price_id=price_id)
    except Exception:
        current_app.logger.exception("Post-checkout subscription reconcile failed")
    # --- END: Post-checkout Stripe reconcile ---

    db.session.commit()

    # One-time post-checkout nudge on Home
    session["post_checkout_nudge"] = True
    session["current_org_id"] = user.org_id
    login_user(user)
    flash("Password set. Welcome!", "success")
    return redirect(url_for("main.home"))

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