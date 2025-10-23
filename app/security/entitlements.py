from functools import wraps
from typing import Callable
from flask import abort
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
