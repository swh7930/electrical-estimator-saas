from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from flask import current_app

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()

# default_limits can be a callable (evaluated in app context)
def _config_limits():
    # Accept string "200 per day;50 per hour" or list ["200 per day", "50 per hour"]
    raw = current_app.config.get("RATELIMIT_DEFAULT") or []
    if isinstance(raw, str):
        return [s.strip() for s in raw.split(";") if s.strip()]
    return raw

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",         # dev default; swap to Redis in prod
    default_limits=_config_limits,    # <-- v3-safe, evaluated per-request
)

mail = Mail()
