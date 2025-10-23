import os
import hmac
import hashlib
from datetime import datetime
from flask import request, jsonify, abort, current_app
from . import bp
from app.extensions import db, csrf
from app.models import EmailLog
import json

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
