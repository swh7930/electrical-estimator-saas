import os
from flask import Flask

# Load .env only for local/dev. In prod, env vars come from the platform.
if os.getenv("APP_ENV", "development") != "production":
    from dotenv import load_dotenv
    # Always load .env if present and override any pre-set envs (prod: no .env → no-op)
    load_dotenv(".env", override=True)


from .config import get_config
from .extensions import db, migrate, csrf, login_manager, limiter, mail

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Config: clean, explicit, class-based
    app.config.from_object(get_config())

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db, directory="migrations")
    csrf.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)

    # Minimal placeholder until real auth is wired
    @login_manager.user_loader
    def load_user(user_id):
        return None

    # Blueprints
    from .blueprints.dashboard import bp as dashboard_bp
    from .blueprints.auth import bp as auth_bp
    from .blueprints.admin import bp as admin_bp
    from .blueprints.api import bp as api_bp
    from .blueprints.estimator import bp as estimator_bp
    from .blueprints.main import bp as main_bp
    from app.blueprints.estimates import bp as estimates_bp
    from app.blueprints.libraries import bp as libraries_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(estimator_bp, url_prefix="/estimator")
    app.register_blueprint(main_bp)
    app.register_blueprint(estimates_bp)
    app.register_blueprint(libraries_bp)

    # Health + index
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

    return app
