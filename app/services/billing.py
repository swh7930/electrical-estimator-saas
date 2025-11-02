from typing import Dict, Any
from urllib.parse import urljoin
from flask import current_app
from stripe import StripeClient
import hashlib, json


def _client() -> StripeClient:
    key = current_app.config.get("STRIPE_SECRET_KEY")
    if not key:
        raise RuntimeError("STRIPE_SECRET_KEY is not configured")
    return StripeClient(key)


def _absolute_url(path: str) -> str:
    base = (current_app.config.get("APP_BASE_URL") or "").rstrip("/") + "/"
    return urljoin(base, path.lstrip("/"))


def make_idempotency_key(*parts: Any) -> str:
    raw = "|".join(str(p) for p in parts)
    return "checkout:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]

def _params_hash(d: Dict[str, Any]) -> str:
    # Stable across runs if params identical; changes when you change fields
    return hashlib.sha256(json.dumps(d, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:16]


def create_checkout_session(*, price_id: str, org_id: int, user_id: int) -> Dict[str, Any]:
    """
    Create a Stripe Checkout Session for a subscription to the given Price.
    Returns: {"id": <session_id>, "url": <redirect_url or None>}
    """
    client = _client()
    params: Dict[str, Any] = {
        "mode": "subscription",
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": _absolute_url("billing/success?session_id={CHECKOUT_SESSION_ID}"),
        "cancel_url": _absolute_url("billing/cancelled"),

        # Tax (env‑controlled; enable for launch)
        "automatic_tax": {"enabled": bool(current_app.config.get("ENABLE_STRIPE_TAX", True))},

        # **New for checkout‑first**
        "billing_address_collection": "required",
        "phone_number_collection": {"enabled": True},
        "tax_id_collection": {"enabled": True},
        "custom_fields": [{
            "key": "company",
            "label": {"type": "custom", "custom": "Company"},
            "type": "text",
            "optional": False
        }],

        # Webhook context + trial
        "metadata": {"org_id": str(org_id), "user_id": str(user_id)},
        "subscription_data": {
            "trial_period_days": 3,
            "metadata": {"org_id": str(org_id), "user_id": str(user_id)},
        },
    }
    # Param-aware idempotency: new key whenever you change Checkout params
    idem = make_idempotency_key(
        "checkout", "v3",  # bump once to break old collisions
        org_id, user_id, price_id,
        _params_hash(params),
    )
    session = client.checkout.sessions.create(params=params, options={"idempotency_key": idem})
    return {"id": session.id, "url": getattr(session, "url", None)}


def create_portal_session(*, stripe_customer_id: str) -> Dict[str, Any]:
    """Create a Stripe Customer Portal session for an existing Customer."""
    client = _client()
    params = {
        "customer": stripe_customer_id,
        "return_url": _absolute_url("billing"),
    }
    session = client.billing_portal.sessions.create(params)
    return {"url": session.url}
