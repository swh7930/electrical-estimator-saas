from flask import render_template
from . import bp

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
