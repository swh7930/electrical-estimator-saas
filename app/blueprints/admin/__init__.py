from flask import Blueprint

bp = Blueprint("admin", __name__, template_folder="templates")

from flask_login import current_user
from flask import request, redirect, url_for

@bp.before_request
def _require_login_admin():
    if current_user.is_authenticated:
        return None
    return redirect(url_for("auth.login_get", next=request.url))


# Import submodules so their routes register on the same bp
from . import assemblies

from . import settings