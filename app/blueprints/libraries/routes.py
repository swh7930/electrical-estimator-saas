from flask import render_template
from . import bp

@bp.get("/materials")
def materials():
    return render_template("materials/index.html")

# Stubs now so sidebar won’t 404 when we wire them later
@bp.get("/dje")
def dje():
    return render_template("dje/index.html")

@bp.get("/customers")
def customers():
    return render_template("customers/index.html")
