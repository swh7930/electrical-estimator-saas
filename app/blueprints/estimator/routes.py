from . import bp

@bp.get("/")
def index():
    return "Estimator OK", 200
