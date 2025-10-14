from flask import render_template
from . import bp

@bp.get("/")
def home():
    return render_template("home.html")

# --- TEMPORARY PREVIEW ROUTES (visual only) ---

@bp.get("/home-cards")
def home_cards():
    return render_template("home_alt_cards.html")

@bp.get("/home-sidebar")
def home_sidebar():
    return render_template("home_alt_sidebar.html")
