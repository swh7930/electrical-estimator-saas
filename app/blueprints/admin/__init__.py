from flask import Blueprint

bp = Blueprint("admin", __name__, url_prefix="/admin")

# Import submodules so their routes register on the same bp
from . import assemblies  # noqa: E402,F401
# (later you can add: from . import estimator, users, etc.)
