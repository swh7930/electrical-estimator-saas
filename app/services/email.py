from typing import Optional, Dict, Any
from urllib.parse import urljoin
from flask import current_app, render_template
from flask_mail import Message
from app.extensions import db, mail
from app.models import EmailLog
from . import tokens

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
        template="reset",
        context=ctx,
        user_id=getattr(user, "id", None),
    )
