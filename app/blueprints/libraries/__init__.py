from flask import Blueprint

bp = Blueprint("libraries", __name__)

from . import routes  # noqa: E402,F401
