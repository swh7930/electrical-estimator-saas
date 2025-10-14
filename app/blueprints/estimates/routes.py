from flask import render_template
from . import bp

@bp.get("/")
def index():
    return render_template("estimates/index.html")

@bp.get("/new")
def new():
    return render_template("estimates/new.html")  # stub for later

@bp.get("/fast")
def fast():
    return render_template("estimates/fast.html")  # stub for later

@bp.get("/<int:estimate_id>")
def view(estimate_id):
    return render_template("estimates/view.html", estimate_id=estimate_id)  # stub for later
