from functools import wraps
from flask import abort, session, request
from flask_login import current_user
from app.extensions import db
from app.models.org_membership import OrgMembership, ROLE_OWNER, ROLE_ADMIN

def _current_org_id():
    oid = session.get("current_org_id")
    if not oid and getattr(current_user, "is_authenticated", False):
        oid = getattr(current_user, "org_id", None)
    return oid

def require_member(fn):
    @wraps(fn)
    def _wrap(*args, **kwargs):
        if not current_user.is_authenticated:
            return _abort_smart(401)
        org_id = _current_org_id()
        if not org_id:
            return _abort_smart(401)
        m = db.session.query(OrgMembership).filter_by(org_id=org_id, user_id=current_user.id).one_or_none()
        if not m:
            return _abort_smart(404)  # anti-enumeration
        return fn(*args, **kwargs)
    return _wrap

def role_required(*roles):
    def deco(fn):
        @wraps(fn)
        def _wrap(*args, **kwargs):
            if not current_user.is_authenticated:
                return _abort_smart(401)
            org_id = _current_org_id()
            if not org_id:
                return _abort_smart(401)
            m = db.session.query(OrgMembership).filter_by(org_id=org_id, user_id=current_user.id).one_or_none()
            if not m:
                return _abort_smart(404)
            if m.role not in roles:
                return _abort_smart(403)
            return fn(*args, **kwargs)
        return _wrap
    return deco

def _abort_smart(code: int):
    # If the client asked for JSON, return a JSON-shaped error
    accept = (request.headers.get("Accept") or "").lower()
    if "application/json" in accept or request.path.endswith(".json"):
        from flask import jsonify
        return jsonify({"error": {401: "unauthorized", 403: "forbidden", 404: "not_found"}[code], "code": code}), code
    abort(code)
