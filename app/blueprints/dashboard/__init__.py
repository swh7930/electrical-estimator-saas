from flask import Blueprint

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

from . import routes  # noqa: E402,F401 (import after bp to avoid circulars)
