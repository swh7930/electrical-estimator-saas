from flask import Blueprint

# Match your existing style (like estimator/__init__.py)
bp = Blueprint("main", __name__, template_folder="templates")

# Import submodules so their @bp.route decorators register
from . import routes  # noqa: E402,F401
