from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = "auth.login_get"

# Key: logged-in user-id; otherwise client IP
from flask_limiter.util import get_remote_address

def _rate_limit_key():
    try:
        # Lazy import avoids circulars during app init
        from flask_login import current_user
        if getattr(current_user, "is_authenticated", False) and getattr(current_user, "id", None):
            return f"user:{current_user.id}"
    except Exception:
        pass
    return get_remote_address()

# Storage is configured in create_app() via limiter.init_app(...).
limiter = Limiter(key_func=_rate_limit_key)

mail = Mail()
