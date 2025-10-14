from flask import Blueprint
bp = Blueprint("estimator", __name__, template_folder="templates")
# Import view + API modules so their @bp.route decorators run
# (order doesn’t matter; importing is what registers routes)
from . import routes          # page views: /estimator, /estimator/dje, etc.
from . import api_materials   # /estimator/api/material-types, /material_descriptions
from . import api_dje         # /estimator/api/dje-*