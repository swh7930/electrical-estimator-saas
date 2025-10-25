from flask import Blueprint, render_template, request, redirect, current_app, abort
from flask_login import login_required, current_user
from app.extensions import limiter
from app.models import Subscription, BillingCustomer, Org
from app.services.billing import create_checkout_session, create_portal_session
from app.services import billing as billing_service

billing_bp = Blueprint("billing", __name__, template_folder="../../templates/billing")


def create_checkout_session(price_id: str, org_id: int):
    org = Org.query.get(org_id)
    if not org:
        abort(400, description="Org not found")
    # pass the Org object; the service can use org.id safely
    return billing_service.create_checkout_session(
        price_id=price_id,
        org=org,
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

    payload = create_checkout_session(price_id, org_id)
    url = payload.get("url")
    if not url:
        abort(502, description="Could not create checkout session")
    # 303 to allow re-POST safely and follow to Stripe-hosted page
    return redirect(url, code=303)


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
    return render_template("billing/success.html")


@billing_bp.get("/cancelled")
@login_required
def cancelled():
    return render_template("billing/cancelled.html")
