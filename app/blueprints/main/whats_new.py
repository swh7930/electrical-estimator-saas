# app/blueprints/main/whats_new.py
from flask import render_template
from . import bp  # main blueprint

@bp.get("/whats-new")
def whats_new():
    # Design-only stub (no logic)
    return render_template("whats_new.html")
