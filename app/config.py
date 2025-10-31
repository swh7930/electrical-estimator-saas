import os

class BaseConfig:
    # Secrets (env in prod; dev/test may use defaults)
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-not-secure")
    WTF_CSRF_SECRET_KEY = SECRET_KEY
    WTF_CSRF_TIME_LIMIT = None  # avoid surprise expirations during long edits

    # Database (env in prod; dev/test may use default)
    try:
        from dotenv import dotenv_values
        _ENV_FALLBACK = dotenv_values(".env")
    except Exception:
        _ENV_FALLBACK = {}
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or _ENV_FALLBACK.get("DATABASE_URL") or "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Logging / misc
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

    # Cookies: secure-by-default
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"  # good balance; can tune per env

    # Flask-Limiter default: off globally; prefer per-route limits
    RATELIMIT_DEFAULT = None
    
    # --- Mail ---
    MAIL_SERVER = os.getenv("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = (os.getenv("MAIL_USE_TLS", "true").lower() == "true")
    MAIL_USE_SSL = (os.getenv("MAIL_USE_SSL", "false").lower() == "true")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", 'Electrical Estimator <no-reply@local.test>')
    MAIL_SUPPRESS_SEND = (os.getenv("MAIL_SUPPRESS_SEND", "false").lower() == "true")

    # Used for absolute links in emails (must be https in prod)
    APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:5000")
    
    # --- Analytics (M4: SEO & Analytics) ---
    PLAUSIBLE_DOMAIN = os.getenv("PLAUSIBLE_DOMAIN", "")
    
    # --- SEO (titles/descriptions used in base template) ---
    SITE_NAME = os.getenv("SITE_NAME", "KMT Electrical Estimator")
    SITE_DESCRIPTION = os.getenv(
        "SITE_DESCRIPTION",
        "Fast, accurate electrical estimating — libraries & assemblies, PDF/CSV exports, and Pro billing."
    )

    # --- Stripe (Billing) ---
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

    # Price IDs (per environment via env vars)
    STRIPE_PRICE_PRO_MONTHLY = os.getenv("STRIPE_PRICE_PRO_MONTHLY")
    STRIPE_PRICE_PRO_ANNUAL = os.getenv("STRIPE_PRICE_PRO_ANNUAL")
    STRIPE_PRICE_ELITE_MONTHLY = os.getenv("STRIPE_PRICE_ELITE_MONTHLY")
    STRIPE_PRICE_ELITE_ANNUAL = os.getenv("STRIPE_PRICE_ELITE_ANNUAL")

    # Taxes: we use exclusive pricing; Stripe Tax computes/collects at checkout/invoice
    ENABLE_STRIPE_TAX = (os.getenv("ENABLE_STRIPE_TAX", "true").lower() == "true")

    # Token salt for email flows
    EMAIL_TOKEN_SALT = os.getenv("EMAIL_TOKEN_SALT", "email-token-v1")

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG")
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    MAIL_SUPPRESS_SEND = True

class ProductionConfig(BaseConfig):
    DEBUG = False
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "WARNING")
    # REQUIRE env vars in production (fail fast if missing)
    SECRET_KEY = os.environ["SECRET_KEY"]
    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    # allow override if you need "Strict" for purely internal apps
    SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
    MAIL_SUPPRESS_SEND = False

class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False

_ENV_MAP = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}

def get_config():
    env = os.environ.get("APP_ENV", "development").lower()
    return _ENV_MAP.get(env, DevelopmentConfig)

