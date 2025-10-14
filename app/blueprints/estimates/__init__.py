from flask import Blueprint

bp = Blueprint("estimates", __name__, url_prefix="/estimates")

from . import routes  # noqa: E402,F401
