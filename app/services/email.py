from typing import Optional, Dict, Any
from urllib.parse import urljoin
from flask import current_app, render_template
from flask_mail import Message
from app.extensions import db, mail
from app.models import EmailLog
from . import tokens
from datetime import datetime, timedelta

# NEW: suppression lookback window
SUPPRESSION_WINDOW_DAYS = 90

# NEW: derive suppression from recent EmailLog rows
def is_suppressed(to_email: str) -> bool:
    """
    Return True if the address should be suppressed due to a recent bounce/complaint.
    """
    cutoff = datetime.utcnow() - timedelta(days=SUPPRESSION_WINDOW_DAYS)
    q = EmailLog.query.filter(
        EmailLog.to_email == to_email,
        EmailLog.created_at >= cutoff,
        EmailLog.status.in_(("bounced", "complaint")),
    )
    # Using EXISTS for efficiency
    return db.session.query(q.exists()).scalar()

# NEW (only if missing): small helper to persist EmailLog
def _log_email(*, user_id, to_email, template, subject, status, provider_msg_id=None, meta=None):
    entry = EmailLog(
        user_id=user_id,
        to_email=to_email,
        template=template,
        subject=subject,
        provider_msg_id=provider_msg_id,
        status=status,
        meta=meta or {},
    )
    db.session.add(entry)
    db.session.commit()
    return entry

def absolute_url(path: str) -> str:
    base = current_app.config["APP_BASE_URL"].rstrip("/") + "/"
    path = path.lstrip("/")
    return urljoin(base, path)

def send_email(to_email: str, subject: str, template: str, context: Optional[Dict[str, Any]] = None, user_id: Optional[int] = None) -> Optional[str]:
    """
    template: basename under templates/email/ without extension (e.g., 'verify' or 'reset')
    Renders both HTML and plaintext. Returns provider message id if available.
    """
    context = context or {}
    html_body = render_template(f"email/{template}.html", **context)
    text_body = render_template(f"email/{template}.txt", **context)

    msg = Message(
        recipients=[to_email],
        subject=subject,
    )
    msg.body = text_body
    msg.html = html_body

    # Persist an initial log
    elog = EmailLog(
        user_id=user_id,
        to_email=to_email.lower(),
        template=template,
        subject=subject,
        status="queued",
        meta={}
    )
    db.session.add(elog)
    db.session.commit()

    try:
        resp = mail.send(msg)  # Flask-Mail returns None; provider_id capture varies by backend
        provider_id = None
        elog.status = "sent"
        elog.provider_msg_id = provider_id
        db.session.commit()
        return provider_id
    except Exception as ex:
        elog.status = "failed"
        elog.meta = {"error": str(ex)}
        db.session.commit()
        # Re-raise or swallow? We'll swallow—to keep UX consistent.
        return None

def send_verification_email(user, token_ttl_minutes: int = 30) -> None:
    token = tokens.generate("verify", user.email.lower())
    url = absolute_url(f"auth/verify?token={token}")
    ctx = {
        "product_name": "Electrical Estimator",
        "action_url": url,
        "user_name": getattr(user, "name", user.email),
        "support_email": "support@electriciansmentor.com",
        "token_ttl_minutes": token_ttl_minutes,
    }
    send_email(
        to_email=user.email,
        subject="Verify your email",
        to_email = getattr(user, "email", None)
        if to_email and is_suppressed(to_email):
            # Minimal log; structured logs come in 03b.4b
            current_app.logger.info("mail suppressed to %s (recent bounce/complaint)", to_email)
            _log_email(
                user_id=getattr(user, "id", None),
                to_email=to_email,
                template="verify",
                subject=subject,
                status="failed",
                meta={"reason": "suppressed"},
            )
            return {"suppressed": True}
        template="verify",
        context=ctx,
        user_id=getattr(user, "id", None),
    )

def send_password_reset_email(user, token_ttl_minutes: int = 120) -> None:
    token = tokens.generate("reset", user.email.lower())
    url = absolute_url(f"auth/reset?token={token}")
    ctx = {
        "product_name": "Electrical Estimator",
        "action_url": url,
        "user_name": getattr(user, "name", user.email),
        "support_email": "support@electriciansmentor.com",
        "token_ttl_minutes": token_ttl_minutes,
    }
    send_email(
        to_email=user.email,
        subject="Reset your password",
        # Do-not-send gate
        to_email = getattr(user, "email", None)
        if to_email and is_suppressed(to_email):
            current_app.logger.info("mail suppressed to %s (recent bounce/complaint)", to_email)
            _log_email(
                user_id=getattr(user, "id", None),
                to_email=to_email,
                template="reset",
                subject=subject,
                status="failed",
                meta={"reason": "suppressed"},
            )
            return {"suppressed": True}
        template="reset",
        context=ctx,
        user_id=getattr(user, "id", None),
    )
