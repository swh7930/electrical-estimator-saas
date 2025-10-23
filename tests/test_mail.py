import json
import hmac
import hashlib

from app.extensions import db
from app.models import EmailLog
from app.services.email import is_suppressed
from app.services import tokens

def test_email_templates_render_include_action_url(app):
    with app.app_context():
        html = app.jinja_env.get_template("email/verify.html").render(
            action_url="http://example.test/verify?t=abc", user=None
        )
        txt = app.jinja_env.get_template("email/verify.txt").render(
            action_url="http://example.test/verify?t=abc", user=None
        )
        assert "http://example.test/verify?t=abc" in html
        assert "http://example.test/verify?t=abc" in txt

        html2 = app.jinja_env.get_template("email/reset.html").render(
            action_url="http://example.test/reset?t=xyz", user=None
        )
        txt2 = app.jinja_env.get_template("email/reset.txt").render(
            action_url="http://example.test/reset?t=xyz", user=None
        )
        assert "http://example.test/reset?t=xyz" in html2
        assert "http://example.test/reset?t=xyz" in txt2


def _sign(secret: str, timestamp: str, body: bytes) -> str:
    # Matches your _valid_signature: HMAC(secret, f"{timestamp}." + raw_body)
    return hmac.new(secret.encode("utf-8"), (timestamp + ".").encode("utf-8") + body, hashlib.sha256).hexdigest()


def test_webhook_hmac_creates_emaillog_bounce(app, client):
    payload = {
        "event": "bounce",
        "email": "bounced@example.com",
        "message_id": "abc123",
    }
    body = json.dumps(payload).encode("utf-8")
    ts = "1700000000"
    sig = _sign(app.config["EMAIL_WEBHOOK_SECRET"], ts, body)

    resp = client.post(
        "/webhooks/email",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Timestamp": ts,
            "X-Signature": sig,
        },
    )
    assert resp.status_code in (200, 204)

    with app.app_context():
        row = EmailLog.query.filter_by(to_email="bounced@example.com").order_by(EmailLog.id.desc()).first()
        assert row is not None
        assert row.status == "bounced"


def test_is_suppressed_true_for_recent_bounce(app):
    with app.app_context():
        db.session.add(EmailLog(
            user_id=None,
            to_email="toxic@example.com",
            template="unknown",
            subject="",
            status="bounced",
            meta={},
        ))
        db.session.commit()

        assert is_suppressed("toxic@example.com") is True
        assert is_suppressed("new@example.com") is False


def test_token_ttl_expiry(app, monkeypatch):
    with app.app_context():
        t = tokens.generate("verify", "user@example.com")
        # Should validate with generous max_age
        assert tokens.verify("verify", t, max_age_seconds=60) == "user@example.com"
        # With tiny max_age, immediately treat as expired
        assert tokens.verify("verify", t, max_age_seconds=0) is None
