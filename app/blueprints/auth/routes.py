from . import bp

@bp.get("/")
def index():
    return "Auth OK", 200
