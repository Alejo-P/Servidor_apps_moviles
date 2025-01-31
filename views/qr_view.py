from flask import render_template, Blueprint, url_for
from config import settings as env
import os

qrview_bp = Blueprint('qrview', __name__)

@qrview_bp.route("/qr", methods=["GET"]) # /views/qr
def qr_form():
    # Ruta al archivo JS
    JSPath = url_for('static', filename='js/viewQRs.js')
    
    # Ruta de la imagen en static/assets
    imgPath = url_for('static', filename='assets/delete-forever-svgrepo-com.svg')
    
    return render_template('viewQRs.html', JSfile=JSPath, assetDelete=imgPath)