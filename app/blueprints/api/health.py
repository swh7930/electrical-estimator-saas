from . import bp

@bp.get("/ping")
def ping():
    return {"pong": True}, 200
