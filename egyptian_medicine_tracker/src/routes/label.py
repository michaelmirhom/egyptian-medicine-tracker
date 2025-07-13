from flask import Blueprint, jsonify
from src.models.dailymed import DailyMedLabel

label_bp = Blueprint("label", __name__)

@label_bp.route("/labels/<string:generic>")
def get_label(generic):
    row = DailyMedLabel.query.filter_by(generic=generic.lower()).first_or_404()
    return jsonify(row.to_dict()) 