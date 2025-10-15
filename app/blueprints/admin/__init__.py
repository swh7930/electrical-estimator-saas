from flask import Blueprint

bp = Blueprint("admin", __name__, template_folder="templates")

# Import submodules so their routes register on the same bp
from . import assemblies

from . import settings