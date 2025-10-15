# app/blueprints/main/instructions.py
from flask import render_template
from . import bp  # main blueprint

@bp.get("/instructions")
def instructions():
    # Design-only stub (no logic)
    return render_template("instructions.html")
