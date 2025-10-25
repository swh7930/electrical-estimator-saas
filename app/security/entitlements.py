from functools import wraps
from typing import Callable
from flask import abort, request, redirect, url_for, flash
from flask_login import current_user
from app.models import Subscription

_ACTIVE = {"active", "trialing"}

def require_entitlement(feature_key: str) -> Callable:
    """
    Server-side guard for Pro/Elite features.
    - Requires an org_id on the current user
    - Requires a Subscription with status in {_ACTIVE}
    - Requires feature_key in entitlements_json snapshot
    """
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            org_id = getattr(current_user, "org_id", None)
            if not org_id:
                abort(403, description="Organization required")
            sub = Subscription.query.filter_by(org_id=org_id).first()
            if not (sub and (sub.status in _ACTIVE)):
                abort(403, description="Subscription required")
            entitlements = (sub.entitlements_json or [])
            if feature_key not in entitlements:
                abort(403, description="Feature not included in current plan")
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# --- Coarse subscription gating (HTML redirect vs JSON 403) ---

def enforce_active_subscription():
    """
    Returns None when allowed; otherwise a Response redirect (HTML) or (payload, 403) for JSON.
    Policy:
      - Allowed: status in {"active","trialing"}.
      - Blocked: past_due, incomplete, incomplete_expired, unpaid, canceled, or no sub.
    """
    org_id = getattr(current_user, "org_id", None)
    # This helper is only called *after* an auth/login gate in blueprints.
    # If somehow no org, treat as blocked.
    sub = Subscription.query.filter_by(org_id=org_id).first() if org_id else None
    is_active = bool(sub and (sub.status in _ACTIVE))

    if is_active:
        return None

    # Match the app's JSON detection style (see 429 handler)
    wants_json = (
        "application/json" in (request.headers.get("Accept") or "").lower()
        or request.is_json
        or request.path.endswith(".json")
        or request.path.endswith(".csv")
    )
    if wants_json:
        return ({"error": "entitlement_required", "missing": "active_subscription"}, 403)

    flash("A paid subscription is required to use this feature.", "warning")
    return redirect(url_for("billing.index"))

def require_active_subscription(fn: Callable):
    """Decorator form (used rarely; we’ll prefer blueprint-level before_request)."""
    @wraps(fn)
    def _wrap(*args, **kwargs):
        resp = enforce_active_subscription()
        if resp is not None:
            return resp
        return fn(*args, **kwargs)
    return _wrap
