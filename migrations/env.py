from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
import os

# Alembic Config object; provides access to .ini values
config = context.config

# Configure Python logging
cfg_path = config.config_file_name
if cfg_path and os.path.exists(cfg_path):
    fileConfig(cfg_path)

# Build the Flask app (factory) and get canonical metadata
try:
    # When running via `flask db ...`, an app context may already exist
    from flask import current_app

    app = current_app._get_current_object()
except Exception:
    # Direct Alembic CLI usage: create the app explicitly
    from app import create_app

    app = create_app()

from app.extensions import db

with app.app_context():
    # ── NEW: load ALL model modules so tables/Indexes are registered on db.metadata
    import importlib, pkgutil

    try:
        import app.models as models  # your models package

        for m in pkgutil.iter_modules(models.__path__):
            importlib.import_module(f"app.models.{m.name}")
    except Exception:
        # If there's no models package, it's harmless — continue
        pass
    # Single source of truth for autogenerate
    target_metadata = db.metadata
    sqlalchemy_url = app.config.get("SQLALCHEMY_DATABASE_URI")

# Optional allowlist: comma-separated index names you explicitly permit Alembic to drop
_DROP_INDEX_ALLOWLIST = {
    name.strip()
    for name in os.getenv("ALEMBIC_DROP_INDEX_ALLOWLIST", "").split(",")
    if name.strip()
}


def _safe_include_object(object, name, type_, reflected, compare_to):
    """
    Keep Alembic from proposing destructive index drops during autogenerate.

    - If an INDEX is present in the database (reflected=True) but *not* in ORM metadata (compare_to is None),
      Alembic would normally propose a DROP. We skip those unless the index name is allowlisted.
    - All other objects (tables, columns, constraints) are included as usual.
    - New/changed indexes that *are* in metadata still generate CREATE/ALTER as expected.
    """
    if type_ == "index":
        if name in _DROP_INDEX_ALLOWLIST:
            return True
        if reflected and compare_to is None:  # DB has it; ORM doesn't → skip DROP
            return False
    return True


# Ensure Alembic knows the DB URL (offline mode uses this)
if sqlalchemy_url:
    config.set_main_option("sqlalchemy.url", sqlalchemy_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_object=_safe_include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_object=_safe_include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
