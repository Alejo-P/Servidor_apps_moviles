from flask import render_template, Blueprint, send_from_directory, jsonify, url_for
from config import settings as env
import os

qrview_bp = Blueprint('qrview', __name__)

@qrview_bp.route("/qr", methods=["GET"]) # /views/qr
def qr_form():
    # Ruta al archivo JS
    JSPath = url_for('static', filename='js/viewQRs.js')
    
    return render_template('viewQRs.html', JSfile=JSPath)