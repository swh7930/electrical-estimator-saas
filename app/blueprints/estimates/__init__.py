from flask import Blueprint

bp = Blueprint("estimates", __name__, url_prefix="/estimates")

from . import routes