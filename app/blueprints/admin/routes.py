from . import bp

@bp.get("/")
def index():
    return "Admin OK", 200
