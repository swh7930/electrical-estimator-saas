import logging
from logging.config import fileConfig
import os
import importlib
import pkgutil
from pathlib import Path

from flask import current_app
from alembic import context

# Alembic Config object (reads alembic.ini)
config = context.config

# Logging (robust: works with alembic.ini in migrations/ or in repo root)
def _init_logging():
    ini = config.config_file_name  # what Alembic thinks the INI is
    if ini and Path(ini).exists():
        fileConfig(ini)
        return
    # Try repo-root alembic.ini (…/migrations/env.py -> parents[1] is repo root)
    root_ini = Path(__file__).resolve().parents[1] / "alembic.ini"
    if root_ini.exists():
        fileConfig(str(root_ini))
        return
    # Fallback: don't crash if no INI present
    logging.basicConfig(level=logging.INFO)

_init_logging()
logger = logging.getLogger("alembic.env")

# ──────────────────────────────────────────────────────────────────────────────
# Flask-Migrate v4 helpers (correct for SQLAlchemy 2.x)
# ──────────────────────────────────────────────────────────────────────────────
def get_engine():
    try:
        # Flask-SQLAlchemy < 3.x or Alchemical
        return current_app.extensions["migrate"].db.get_engine()
    except (TypeError, AttributeError):
        # Flask-SQLAlchemy >= 3.x
        return current_app.extensions["migrate"].db.engine


def get_engine_url():
    try:
        return get_engine().url.render_as_string(hide_password=False).replace("%", "%%")
    except AttributeError:
        return str(get_engine().url).replace("%", "%%")


# Alembic needs a URL in offline mode
config.set_main_option("sqlalchemy.url", get_engine_url())

# SQLAlchemy metadata via Flask-Migrate
target_db = current_app.extensions["migrate"].db


def get_metadata():
    # Flask-Migrate may expose multiple metadatas; default to None key
    if hasattr(target_db, "metadatas"):
        return target_db.metadatas[None]
    return target_db.metadata

# ──────────────────────────────────────────────────────────────────────────────
# ADD: model auto-import (ensures all models/Indexes are registered)
# ──────────────────────────────────────────────────────────────────────────────
def _autoload_models():
    """
    Import all modules in app.models so Alembic 'autogenerate'
    sees every table/index/constraint.
    """
    try:
        import app.models as models_pkg
        for m in pkgutil.iter_modules(models_pkg.__path__):
            importlib.import_module(f"app.models.{m.name}")
        logger.info("Auto-loaded models from app.models/*")
    except Exception as e:
        logger.warning("Model autoload skipped or partial: %s", e)


# ──────────────────────────────────────────────────────────────────────────────
# ADD: safe autogenerate settings (avoid accidental index drops)
# ──────────────────────────────────────────────────────────────────────────────
_DROP_INDEX_ALLOWLIST = {
    name.strip()
    for name in os.getenv("ALEMBIC_DROP_INDEX_ALLOWLIST", "").split(",")
    if name.strip()
}

def _include_object(object, name, type_, reflected, compare_to):
    """
    Prevent autogenerate from proposing destructive index DROPs unless allowlisted.
    """
    if type_ == "index":
        if name in _DROP_INDEX_ALLOWLIST:
            return True
        if reflected and compare_to is None:
            # Index exists in DB but not in metadata -> skip DROP
            return False
    return True


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    # Load models so metadata is complete
    _autoload_models()

    context.configure(
        url=url,
        target_metadata=get_metadata(),
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
        include_object=_include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode'."""
    # Prevent no-op file creation
    def process_revision_directives(context_, revision, directives):
        if getattr(config.cmd_opts, "autogenerate", False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info("No changes in schema detected.")

    conf_args = current_app.extensions["migrate"].configure_args
    # Ensure our callbacks / compare options are present
    conf_args = {
        **conf_args,
        "process_revision_directives": conf_args.get(
            "process_revision_directives", process_revision_directives
        ),
        "compare_type": True,
        "compare_server_default": True,
        "include_object": _include_object,
        "target_metadata": get_metadata(),
    }

    # Load models so metadata is complete
    _autoload_models()

    connectable = get_engine()
    with connectable.connect() as connection:
        context.configure(connection=connection, **conf_args)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
