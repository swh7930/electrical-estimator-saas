import os
from flask import Flask, render_template, request, jsonify

# Load .env only for local/dev. In prod, env vars come from the platform.
if os.getenv("APP_ENV", "development") != "production":
    from dotenv import load_dotenv
    # Always load .env if present and override any pre-set envs (prod: no .env → no-op)
    load_dotenv(".env", override=True)


from .config import get_config
from .extensions import db, migrate, csrf, login_manager, limiter, mail
from .security import init_security
from .observability import init_logging, init_sentry

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    
    # ---- S3-03b.5 Rate Limiting storage configuration ----
    app_env = (os.getenv("APP_ENV", "development") or "development").lower()
    use_redis = app_env in ("staging", "production")
    storage_uri = os.environ.get("REDIS_URL") if use_redis else "memory://"
    if use_redis and not storage_uri:
        # Hard fail in stage/prod so we never silently run without RL storage
        raise RuntimeError("REDIS_URL is required in staging/production for rate limiting")
    # -------------------------------------------------------

    # Configure Flask-Limiter via config (compatible with your installed version)
    app.config["RATELIMIT_STORAGE_URI"] = storage_uri
    app.config.setdefault("RATELIMIT_DEFAULTS", ["1000 per hour"])
    app.config.setdefault("RATELIMIT_HEADERS_ENABLED", True)
    
    # Config: clean, explicit, class-based
    app.config.from_object(get_config())
    
    # --- M3: Observability & Security ---
    init_logging(app)
    init_sentry(app)

    # Apply HTTPS, HSTS & CSP only in staging/production
    app_env = app.config.get("APP_ENV", os.getenv("APP_ENV", "development")).lower()
    if app_env in ("staging", "production"):
        init_security(app)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db, directory="migrations")
    csrf.init_app(app)
    login_manager.init_app(app)
    # Global soft fallback: catch outliers without harming normal UX
    limiter.init_app(app)
    mail.init_app(app)

    # Blueprints (explicit, consistent prefixes)
    from .blueprints.dashboard import bp as dashboard_bp
    from .blueprints.auth import bp as auth_bp
    from .blueprints.admin import bp as admin_bp
    from .blueprints.api import bp as api_bp
    from .blueprints.estimator import bp as estimator_bp
    from .blueprints.main import bp as main_bp
    from .blueprints.estimates import bp as estimates_bp
    from .blueprints.libraries import bp as libraries_bp
    from .blueprints.webhooks import bp as webhooks_bp
    from app.blueprints.billing.routes import billing_bp
    

    # Core / marketing
    app.register_blueprint(main_bp)                         # "/"
    app.register_blueprint(dashboard_bp, url_prefix="/dash")
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # Product areas
    app.register_blueprint(estimator_bp, url_prefix="/estimator")
    app.register_blueprint(estimates_bp,  url_prefix="/estimates")
    app.register_blueprint(libraries_bp,  url_prefix="/libraries")  # materials, dje, customers

    # Admin & API
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp,   url_prefix="/api")
    
    # Webhooks
    app.register_blueprint(webhooks_bp, url_prefix="/webhooks")
    app.register_blueprint(billing_bp, url_prefix="/billing")
    
    # Exempt Flask's static endpoint from default/global limits
    try:
        limiter.exempt(app.view_functions["static"])
    except KeyError:
        pass
   
    # Template globals (shared across all templates)
    from datetime import datetime, timezone

    @app.context_processor
    def inject_globals():
        """Inject global template variables."""
        root = app.root_path
        def mtime_fmt(rel_path: str) -> str:
            """Return 'Month D, YYYY' from a template's mtime; fallback to current date."""
            try:
                ts = os.path.getmtime(os.path.join(root, "templates", rel_path))
                return datetime.fromtimestamp(ts).strftime("%B %-d, %Y")  # *nix day format
            except Exception:
                # Windows strftime doesn't support %-d; try a portable format:
                try:
                    return datetime.fromtimestamp(ts).strftime("%B %d, %Y")
                except Exception:
                    return datetime.now(timezone.utc).strftime("%B %d, %Y")
                
        # Authorization flag for templates (admin/owner can write)
        can_write = False
        try:
            from flask_login import current_user
            from flask import session as _session
            from app.models.org_membership import OrgMembership
            from app.extensions import db as _db
            if getattr(current_user, "is_authenticated", False):
                _org_id = _session.get("current_org_id") or getattr(current_user, "org_id", None)
                if _org_id:
                    _m = _db.session.query(OrgMembership).filter_by(org_id=_org_id, user_id=current_user.id).one_or_none()
                    can_write = bool(_m and _m.role in ("admin", "owner"))
        except Exception:
            can_write = False

        # Subscription banner (contextual)
        billing_banner = {"show": False}
        try:
            from flask_login import current_user  # already imported above; safe to repeat locally
            from flask import session as _session, url_for as _url_for
            from app.models.subscription import Subscription as _Sub
            if getattr(current_user, "is_authenticated", False):
                _org_id = _session.get("current_org_id") or getattr(current_user, "org_id", None)
                if _org_id:
                    _s = _Sub.query.filter_by(org_id=_org_id).first()
                    is_active = bool(_s and (_s.status in {"active","trialing"}))
                    if not is_active:
                        # Admins (can_write) get CTA to plans; non-admins get a heads-up only.
                        if can_write:
                            billing_banner = {
                                "show": True,
                                "message": "Unlock Estimator with Pro to use the app.",
                                "cta_url": _url_for("billing.index"),
                                "cta_text": "View plans",
                            }
                        else:
                            billing_banner = {
                                "show": True,
                                "message": "Your organization doesn’t have an active subscription. Please contact an admin.",
                                "cta_url": None,
                                "cta_text": None,
                            }
        except Exception:
            billing_banner = {"show": False}
        
        return {
            "current_year": datetime.now(timezone.utc).year,
            "last_updated_terms": mtime_fmt("terms.html"),
            "last_updated_privacy": mtime_fmt("privacy.html"),
            "can_write": can_write,
            "billing_banner": billing_banner,
        }

    @limiter.exempt
    # Health
    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}, 200
    
    # Error handlers (minimal)
    @app.errorhandler(404)
    def not_found(e):
        return ("Not Found", 404)

    @app.errorhandler(500)
    def server_error(e):
        return ("Internal Server Error", 500)
    
    # CSRF error handler (clean 400 instead of generic 500)
    from flask_wtf.csrf import CSRFError
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        # If you have templates/errors/csrf_error.html you can render it instead:
        # return render_template("errors/csrf_error.html", reason=e.description), 400
        return (f"CSRF validation failed: {e.description}", 400)
    
    @app.errorhandler(403)
    def forbidden(e):
        # For HTML requests, render a page; JSON is handled by policy decorators explicitly.
        accept = (request.headers.get("Accept") or "").lower()
        if "application/json" in accept:
            return {"error": "forbidden", "code": 403}, 403
        return render_template("errors/403.html"), 403
    
    # 429 Too Many Requests — consistent JSON/HTML with Retry-After
    @app.errorhandler(429)
    def too_many_requests(e):
        retry_after = getattr(e, "retry_after", None)
        headers = {}
        if retry_after is not None:
            headers["Retry-After"] = str(int(retry_after))
        wants_json = (
            "application/json" in (request.headers.get("Accept") or "").lower()
            or request.is_json
            or request.path.endswith(".json")
        )
        if wants_json:
            payload = {"error": "rate_limited", "code": 429}
            if retry_after is not None:
                payload["retry_after"] = int(retry_after)
            return (payload, 429, headers)
        # HTML
        return (render_template("errors/429.html", retry_after=retry_after), 429, headers)
    
    # CLI commands (ops-grade utilities)
    from .cli import register_cli
    register_cli(app)

    return app
