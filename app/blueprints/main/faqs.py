# app/blueprints/main/faqs.py
from flask import render_template
from . import bp  # main blueprint

@bp.get("/faqs")
def faqs():
    # Design-only stub (no logic)
    return render_template("faqs.html")
