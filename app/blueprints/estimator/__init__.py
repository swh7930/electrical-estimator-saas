from flask import Blueprint
bp = Blueprint("estimator", __name__, url_prefix="/estimator")
from . import routes  # noqa: E402,F401
