# app/blueprints/admin/settings.py
from flask import render_template
from . import bp  # the single admin blueprint

@bp.get("/settings")
def settings():
    # Design-only stub (no logic)
    return render_template("admin/settings.html")
