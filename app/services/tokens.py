from typing import Optional
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import current_app

def _serializer() -> URLSafeTimedSerializer:
    secret = current_app.config["SECRET_KEY"]
    salt = current_app.config.get("EMAIL_TOKEN_SALT", "email-token-v1")
    return URLSafeTimedSerializer(secret_key=secret, salt=salt)

def generate(kind: str, identity: str) -> str:
    """
    kind: 'verify' or 'reset'
    identity: email (lowercased) or user id string – we use email for portability.
    """
    return _serializer().dumps({"k": kind, "i": identity})

def verify(kind: str, token: str, max_age_seconds: int) -> Optional[str]:
    try:
        data = _serializer().loads(token, max_age=max_age_seconds)
    except (BadSignature, SignatureExpired):
        return None
    if data.get("k") != kind:
        return None
    return data.get("i")
