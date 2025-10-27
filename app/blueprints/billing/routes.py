from flask import Blueprint, render_template, request, redirect, current_app, abort, jsonify, url_for, flash
from flask_login import login_required, current_user
from app.extensions import limiter
from app.models import Subscription, BillingCustomer, Org
from app.services.billing import create_portal_session
from app.services import billing as billing_service
import stripe

billing_bp = Blueprint("billing", __name__, template_folder="../../templates/billing")

def _checkout_url(session_obj):
    # service may return a dict or a Stripe Session object
    if isinstance(session_obj, dict):
        return session_obj.get("url")
    return getattr(session_obj, "url", None)

def create_checkout_session(price_id: str, org_id: int):
    org = Org.query.get(org_id)
    if not org:
        abort(400, description="Org not found")
    # pass the Org object; the service can use org.id safely
    return billing_service.create_checkout_session(
        price_id=price_id,
        org_id=org_id,
        user_id=current_user.id,
    )

@billing_bp.get("")
@billing_bp.get("/")
@login_required
def index():
    org_id = getattr(current_user, "org_id", None)
    if not org_id:
        abort(403)

    sub = Subscription.query.filter_by(org_id=org_id).first()
    is_active = bool(sub and sub.status in ("active", "trialing"))

    cfg = current_app.config
    ctx = {
        "is_active": is_active,
        "price_pro_monthly": cfg.get("STRIPE_PRICE_PRO_MONTHLY"),
        "price_pro_annual": cfg.get("STRIPE_PRICE_PRO_ANNUAL"),
        "price_elite_monthly": cfg.get("STRIPE_PRICE_ELITE_MONTHLY"),
        "price_elite_annual": cfg.get("STRIPE_PRICE_ELITE_ANNUAL"),
        "has_customer": BillingCustomer.query.filter_by(org_id=org_id).first() is not None,
    }
    return render_template("billing/index.html", **ctx)


@billing_bp.post("/checkout")
@limiter.limit("10/minute")
@login_required
def checkout():
    org_id = getattr(current_user, "org_id", None)
    if not org_id:
        abort(403)

    # Block duplicate purchases if already active/trialing
    sub = Subscription.query.filter_by(org_id=org_id).first()
    if sub and sub.status in ("active", "trialing"):
        abort(409, description="Subscription already active")

    price_id = (request.form.get("price_id") or "").strip()
    if not price_id:
        abort(400, description="price_id is required")

    try:
        payload = create_checkout_session(price_id, org_id)
    except Exception as e:
        # Log the real error (and surface it in staging so we don't have to hunt in Render)
        current_app.logger.exception(
            "billing.checkout.session_create_failed",
            extra={"org_id": org_id, "price_id": price_id, "user_id": current_user.id},
        )
        if current_app.config.get("APP_ENV") in ("staging", "development"):
            return (f"<pre>{e.__class__.__name__}: {e}</pre>", 500)
        abort(502, description="Could not create checkout session")

    url = _checkout_url(payload)
    if not url:
        abort(502, description="Could not create checkout session")
    # 303 to allow re-POST safely and follow to Stripe-hosted page
    return redirect(url, code=303)

@billing_bp.get("/stripe-pk")
@login_required
def stripe_publishable_key():
    """
    Return the publishable key for Stripe.js initialization (safe to expose).
    """
    pk = current_app.config.get("STRIPE_PUBLISHABLE_KEY")
    return jsonify({"publishable_key": pk})

@billing_bp.post("/checkout.json")
@login_required
def checkout_json():
    """
    Create a Checkout Session and return its ID for Stripe.js redirect.
    Mirrors the logic in /billing/checkout but returns JSON instead of 303.
    """
    data = request.get_json(silent=True) or {}
    price_id = data.get("price_id")
    if not price_id:
        return jsonify({"error": "Missing price_id"}), 400

    stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]

    # Reuse your existing success/cancel URLs (adjust names if different)
    success_url = url_for("billing.success", _external=True) + "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = url_for("billing.index", _external=True)

     # Respect the project’s env flag (ENABLE_STRIPE_TAX) for exclusive pricing
    auto_tax_enabled = bool(current_app.config.get("ENABLE_STRIPE_TAX", True))

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            customer_email=(getattr(current_user, "email", None) or None),
            success_url=success_url,              # you already build this via url_for("billing.success") + session_id
            cancel_url=cancel_url,                # you already build this via url_for("billing.index")
            allow_promotion_codes=True,
            automatic_tax={"enabled": auto_tax_enabled},

            # keep the metadata you added — this is what unlocks via webhook
            metadata={
                "org_id": str(getattr(current_user, "org_id", "")),
                "user_id": str(getattr(current_user, "id", "")),
            },
            subscription_data={
                "metadata": {
                    "org_id": str(getattr(current_user, "org_id", "")),
                    "user_id": str(getattr(current_user, "id", "")),
                }
            },
        )
        return jsonify({"sessionId": session["id"]})
    except Exception as e:
        # ensure the frontend gets JSON instead of hanging on an HTML 500
        current_app.logger.exception(
            "billing.checkout_json.session_create_failed",
            extra={"org_id": getattr(current_user, "org_id", None), "price_id": price_id, "user_id": current_user.id},
        )
        user_msg = getattr(e, "user_message", None) or str(e)
        return jsonify({"error": user_msg}), 400

@billing_bp.post("/portal.json")
@limiter.limit("10/minute")
@login_required
def portal_json():
    org_id = getattr(current_user, "org_id", None)
    if not org_id:
        return jsonify({"error": "Forbidden"}), 403

    bc = BillingCustomer.query.filter_by(org_id=org_id).first()
    if not bc:
        return jsonify({"error": "No billing profile for this organization"}), 404

    try:
        payload = create_portal_session(stripe_customer_id=bc.stripe_customer_id)
    except Exception as e:
        current_app.logger.exception(
            "billing.portal_json.session_create_failed",
            extra={"org_id": org_id, "user_id": getattr(current_user, "id", None)},
        )
        user_msg = getattr(e, "user_message", None) or str(e)
        return jsonify({"error": user_msg}), 400

    url = payload.get("url")
    if not url:
        return jsonify({"error": "Could not create portal session"}), 502

    return jsonify({"url": url})

@billing_bp.get("/portal")
@billing_bp.post("/portal")
@limiter.limit("10/minute")
@login_required
def portal():
    org_id = getattr(current_user, "org_id", None)
    if not org_id:
        abort(403)

    bc = BillingCustomer.query.filter_by(org_id=org_id).first()
    if not bc:
        abort(404, description="No billing profile for this organization")

    payload = create_portal_session(stripe_customer_id=bc.stripe_customer_id)
    url = payload.get("url")
    if not url:
        abort(502, description="Could not create portal session")
    return redirect(url, code=303)


@billing_bp.get("/success")
@login_required
def success():
    session_id = request.args.get("session_id")
    if session_id:
        try:
            # Optional sanity (keep your existing style if you already do this)
            stripe.checkout.Session.retrieve(session_id)
        except Exception as e:
            current_app.logger.warning("Checkout success: could not retrieve session %s: %s", session_id, e)

    flash("Your organization has an active subscription.", "success")
    return redirect("/")


@billing_bp.get("/cancelled")
@login_required
def cancelled():
    return render_template("billing/cancelled.html")
