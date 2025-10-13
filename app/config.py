# app/config.py
import os

class BaseConfig:
    # Secrets
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-not-secure")
    WTF_CSRF_SECRET_KEY = SECRET_KEY

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///:memory:")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Logging / misc
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

    # Flask-Limiter default: no global limits; we’ll add per-route later
    RATELIMIT_DEFAULT = None

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG")

class ProductionConfig(BaseConfig):
    DEBUG = False
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "WARNING")

class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")

_ENV_MAP = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}

def get_config():
    env = os.environ.get("APP_ENV", "development").lower()
    return _ENV_MAP.get(env, DevelopmentConfig)
