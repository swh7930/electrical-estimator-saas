import os
import logging
from logging.config import dictConfig

try:
    # optional until installed in staging
    from pythonjsonlogger import jsonlogger  # type: ignore
except Exception:
    jsonlogger = None

def init_logging(app):
    """Structured logs (JSON) in staging/prod; keep default console in dev/tests."""
    app_env = (os.getenv("APP_ENV", "development") or "development").lower()
    if app_env in ("staging", "production"):
        fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
        formatter = "pythonjsonlogger.jsonlogger.JsonFormatter" if jsonlogger else "logging.Formatter"
        dictConfig({
            "version": 1,
            "formatters": {"json": {"()": formatter, "fmt": fmt}},
            "handlers": {"wsgi": {"class": "logging.StreamHandler", "formatter": "json"}},
            "root": {"level": "INFO", "handlers": ["wsgi"]},
        })

def init_sentry(app):
    """Wire Sentry if DSN present; safe no-op otherwise."""
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        sentry_sdk.init(
            dsn=dsn,
            integrations=[FlaskIntegration()],
            traces_sample_rate=float(os.getenv("SENTRY_TRACES", "0.0")),
            profiles_sample_rate=float(os.getenv("SENTRY_PROFILES", "0.0")),
            environment=os.getenv("APP_ENV", "development"),
        )
    except Exception as exc:
        app.logger.warning("Sentry init skipped: %s", exc)
