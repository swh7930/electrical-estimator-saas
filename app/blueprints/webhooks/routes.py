import os
import hmac
import hashlib
from datetime import datetime
from flask import request, jsonify, abort, current_app
from . import bp
from app.extensions import db, csrf
from app.models import EmailLog, BillingEventLog, Subscription, BillingCustomer
import json
import stripe
from app.billing.entitlements import resolve_entitlements

def _valid_signature(raw_body: bytes, timestamp: str, sig: str) -> bool:
    secret = os.getenv("EMAIL_WEBHOOK_SECRET")
    if not secret:
        return False
    mac = hmac.new(secret.encode("utf-8"), (timestamp + ".").encode("utf-8") + raw_body, hashlib.sha256).hexdigest()
    try:
        return hmac.compare_digest(mac, sig)
    except Exception:
        return False

@csrf.exempt
@bp.post("/email")
def email_events():
    # Generic HMAC: X-Timestamp, X-Signature
    timestamp = request.headers.get("X-Timestamp", "")
    signature = request.headers.get("X-Signature", "")
    raw = request.get_data() or b""

    if not _valid_signature(raw, timestamp, signature):
        abort(401)

    payload = request.get_json(force=True, silent=False)
    event = (payload.get("event") or "").lower()           # e.g., "bounce" | "complaint" | "delivered"
    to_email = (payload.get("email") or "").strip().lower()
    provider_msg_id = payload.get("message_id")

    status_map = {
        "bounce": "bounced",
        "complaint": "complaint",
        "delivered": "delivered",
    }
    status = status_map.get(event, "failed" if event else "failed")

    log = EmailLog(
        user_id=None,
        to_email=to_email,
        template=payload.get("template") or "unknown",
        subject=payload.get("subject") or "",
        provider_msg_id=provider_msg_id,
        status=status,
        meta=payload,
        created_at=datetime.utcnow(),
    )
    db.session.add(log)
    db.session.commit()
    
    current_app.logger.info(json.dumps({
        "event": "mail_webhook",
        "to": to_email,
        "status": status,
        "provider_msg_id": provider_msg_id
    }))
    
    return jsonify({"ok": True}), 200

# ----- Stripe Webhook (subscriptions lifecycle) -----
@csrf.exempt
@bp.post("/stripe")
def stripe_webhook():
    """
    Stripe → /webhooks/stripe
    Verifies signature, logs event, idempotently reconciles Subscription/BillingCustomer.
    """
    # 1) Verify signature
    secret = current_app.config.get("STRIPE_WEBHOOK_SECRET")
    if not secret:
        abort(500, description="Stripe webhook secret not configured")

    raw_bytes = request.get_data(cache=False, as_text=False)
    sig_header = request.headers.get("Stripe-Signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload=raw_bytes.decode("utf-8"),
            sig_header=sig_header,
            secret=secret,
        )
        signature_valid = True
    except Exception:
        # Log invalid attempts with a deterministic synthetic id (no payload trust)
        digest = hashlib.sha256(raw_bytes).hexdigest()[:32]
        synthetic_id = f"invalid:{digest}"
        log = BillingEventLog(
            stripe_event_id=synthetic_id,
            type="signature_invalid",
            signature_valid=False,
            payload={},
            created_at=datetime.utcnow(),
        )
        db.session.add(log)
        db.session.commit()
        return jsonify({"error": "invalid_signature"}), 400

    # 2) Idempotency guard (short-circuit if already processed)
    ev_id = event.get("id")
    ev_type = event.get("type")
    if not ev_id or not ev_type:
        return jsonify({"error": "malformed_event"}), 400

    if BillingEventLog.query.filter_by(stripe_event_id=ev_id).first():
        return jsonify({"ok": True, "duplicate": True}), 200

    # 3) Persist raw payload to log (for audit/forensics)
    try:
        payload_json = json.loads(raw_bytes.decode("utf-8"))
    except Exception:
        payload_json = {"_decode_error": True}

    log = BillingEventLog(
        stripe_event_id=ev_id,
        type=ev_type,
        signature_valid=True,
        payload=payload_json,
        created_at=datetime.utcnow(),
    )
    db.session.add(log)
    db.session.commit()

    # 4) Reconcile helpers
    from stripe import StripeClient  # local import to avoid global dependency at import time

    def _client() -> StripeClient:
        key = current_app.config.get("STRIPE_SECRET_KEY")
        if not key:
            raise RuntimeError("STRIPE_SECRET_KEY is not configured")
        return StripeClient(key)

    def _to_dt(ts):
        return datetime.utcfromtimestamp(ts) if ts else None

    def _upsert_customer_and_subscription_from_sub(sub_obj: dict, org_from_meta: int | None = None):
        """
        Upsert BillingCustomer + Subscription from a Stripe subscription object.
        """
        # Resolve org_id
        meta = (sub_obj.get("metadata") or {})
        org_id_val = org_from_meta or meta.get("org_id")
        if not org_id_val:
            # No org context → nothing to do
            return
        try:
            org_id = int(org_id_val)
        except Exception:
            return

        # Upsert BillingCustomer by stripe_customer_id
        cust = sub_obj.get("customer")
        cust_id = cust["id"] if isinstance(cust, dict) else cust
        if not cust_id:
            return

        bc = BillingCustomer.query.filter_by(stripe_customer_id=cust_id).first()
        if not bc:
            bc = BillingCustomer(
                org_id=org_id,
                stripe_customer_id=cust_id,
                billing_email=None,
                default_payment_method=None,
            )
            db.session.add(bc)
        else:
            if not getattr(bc, "org_id", None):
                bc.org_id = org_id

        # First item drives product/price/qty for simple one-price subs
        items = (sub_obj.get("items") or {}).get("data") or []
        if not items:
            db.session.commit()
            return
        first = items[0]
        price = first.get("price") or {}
        price_id = price.get("id")
        product = price.get("product")
        product_id = product["id"] if isinstance(product, dict) else product

        s = Subscription.query.filter_by(org_id=org_id).first()
        if not s:
            s = Subscription(
                org_id=org_id,
                stripe_subscription_id=sub_obj.get("id"),
                product_id=product_id,
                price_id=price_id,
                status=sub_obj.get("status") or "incomplete",
                current_period_end=_to_dt(sub_obj.get("current_period_end")),
                cancel_at=_to_dt(sub_obj.get("cancel_at")),
                cancel_at_period_end=bool(sub_obj.get("cancel_at_period_end")),
                quantity=(first.get("quantity") or 1),
            )
            db.session.add(s)
            s.entitlements_json = resolve_entitlements(product_id=product_id, price_id=price_id)
        else:
            s.stripe_subscription_id = sub_obj.get("id")
            s.product_id = product_id
            s.price_id = price_id
            s.status = sub_obj.get("status") or s.status
            s.current_period_end = _to_dt(sub_obj.get("current_period_end"))
            s.cancel_at = _to_dt(sub_obj.get("cancel_at"))
            s.cancel_at_period_end = bool(sub_obj.get("cancel_at_period_end"))
            s.quantity = (first.get("quantity") or s.quantity or 1)
            s.entitlements_json = resolve_entitlements(product_id=product_id, price_id=price_id)

        db.session.commit()

    def _reconcile_by_subscription_id(sub_id: str, org_from_meta: int | None = None):
        client = _client()
        sub_obj = client.subscriptions.retrieve(sub_id)
        # Stripe objects may need converting to dicts
        if hasattr(sub_obj, "to_dict_recursive"):
            sub_obj = sub_obj.to_dict_recursive()
        _upsert_customer_and_subscription_from_sub(sub_obj, org_from_meta=org_from_meta)

    # 5) Handle event types
    obj = (event.get("data") or {}).get("object") or {}

    try:
        if ev_type == "checkout.session.completed":
            sub_id = obj.get("subscription")
            org_from_meta = (obj.get("metadata") or {}).get("org_id")
            if sub_id:
                _reconcile_by_subscription_id(sub_id, org_from_meta=org_from_meta)

        elif ev_type in ("customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted"):
            # event carries full subscription object
            sub_obj = obj
            if hasattr(sub_obj, "to_dict_recursive"):
                sub_obj = sub_obj.to_dict_recursive()
            _upsert_customer_and_subscription_from_sub(sub_obj, org_from_meta=(sub_obj.get("metadata") or {}).get("org_id"))

        elif ev_type in ("invoice.paid", "invoice.payment_failed"):
            sub_id = obj.get("subscription")
            if sub_id:
                _reconcile_by_subscription_id(sub_id)

        # Other events: ignored for now
    except Exception as e:
        # Attach note and surface 200 to prevent endless Stripe retries; ops can review logs
        log.notes = f"handler_error:{type(e).__name__}"
        db.session.commit()
        current_app.logger.exception("stripe_webhook_handler_error")

    return jsonify({"ok": True}), 200
