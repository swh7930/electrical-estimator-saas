from flask import Blueprint

bp = Blueprint("api", __name__, url_prefix="/api")

from . import health  # noqa: E402,F401
