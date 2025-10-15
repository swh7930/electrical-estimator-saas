# app/blueprints/main/legal.py
from flask import render_template
from . import bp  # main blueprint

@bp.get("/terms")
def terms():
    return render_template("terms.html")

@bp.get("/privacy")
def privacy():
    return render_template("privacy.html")
