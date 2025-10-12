from . import bp

@bp.get("/")
def home():
    return "Dashboard OK", 200
