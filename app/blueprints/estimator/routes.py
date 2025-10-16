from flask import render_template
from . import bp

def _default_percent_ranges():
    # Temporary defaults; we’ll pull these from Settings later
    return dict(
        misc_range=range(0, 21),          # 0–20%
        small_tools_range=range(0, 11),   # 0–10%
        large_tools_range=range(0, 11),   # 0–10%
        waste_theft_range=range(0, 21),   # 0–20%
        sales_tax_range=range(0, 21),     # 0–20%
    )

@bp.context_processor
def inject_estimator_defaults():
    # Inject into every estimator template (Summary, Adjustments, etc.)
    return _default_percent_ranges()

# Main estimator interface
@bp.route("/", methods=["GET"])
def estimator_home():
    return render_template("estimator/estimator.html")

# Adjustments page
@bp.route("/adjustments", methods=["GET"])
def estimator_adjustments():
    return render_template("estimator/adjustments.html")

# DJE (Direct Job Expenses) page
@bp.route("/dje", methods=["GET"])
def estimator_dje():
    return render_template("estimator/dje.html")

# Summary page
@bp.route("/summary", methods=["GET"])
def estimator_summary():
    return render_template("estimator/summary.html")
