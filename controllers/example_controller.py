from flask import Blueprint, jsonify

example_bp = Blueprint('example', __name__)

@example_bp.route("/", methods=["GET"])
def index():
    return jsonify({"message": "Bienvenido a la API"}), 200

