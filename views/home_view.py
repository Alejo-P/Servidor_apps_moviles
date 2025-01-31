from flask import render_template, Blueprint, send_from_directory, jsonify
from config import settings as env

home_bp = Blueprint('home', __name__)

@home_bp.route("/", methods=["GET"]) # /
def home():
    return render_template('index.html')