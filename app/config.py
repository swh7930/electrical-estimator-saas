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

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG")
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False

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

