import os
from flask import Flask

from .extensions import db, migrate, csrf, login_manager, limiter, mail

def create_app():
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # Minimal config so it boots now; will be overridden by real env later
    app.config.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "dev-not-secure"))
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", os.getenv("DATABASE_URL", "sqlite:///:memory:"))
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)
    
     # --- register blueprints ---
    from .blueprints.dashboard import bp as dashboard_bp
    from .blueprints.auth import bp as auth_bp
    from .blueprints.admin import bp as admin_bp
    from .blueprints.api import bp as api_bp
    from .blueprints.estimator import bp as estimator_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(estimator_bp)



    # Temporary smoke route (we'll replace with blueprints next)
    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}, 200

    @app.get("/")
    def index():
        return "OK", 200

    return app
