from flask import render_template, Blueprint, send_from_directory, jsonify, url_for
from config import settings as env
import os

upload_bp = Blueprint('filesView', __name__)

@upload_bp.route("/upload", methods=["GET"]) # /views/upload
def upload_form():
    files_ext =", ".join(env.ALLOWED_EXTENSIONS) # Unir las extensiones permitidas
    
    # Ruta al archivo JS
    JSPath = url_for('static', filename='js/viewUpload.js')
    return render_template('viewUpload.html', extensions=files_ext, JSfile=JSPath)

@upload_bp.route("/pdf/<filename>", methods=["GET"]) # /views/pdf/<filename>
def view_pdf(filename):
    # Verificar si el archivo existe
    if not os.path.exists(os.path.join(env.UPLOAD_FOLDER, filename)):
        return jsonify({"error": "File not found"}), 404

    # Servir el archivo PDF
    return send_from_directory(env.UPLOAD_FOLDER, filename)

@upload_bp.route("/files", methods=["GET"]) # /views/files
def list_files():
    # Listar archivos en la carpeta de subida
    files = os.listdir(env.UPLOAD_FOLDER)
    qr_files = os.listdir(env.QR_FOLDER)
    
    outputFile = []
    for f in files:
        detail = {"name": f, "qr": False}
        for qr in qr_files:
            if f in qr:
                detail["qr"] = True
                break
        outputFile.append(detail)
        
    JSPath = url_for('static', filename='js/viewPDFs.js')
    imgPath = url_for('static', filename='assets/delete-forever-svgrepo-com.svg')
    
    return render_template("viewPDFs.html", files=outputFile, JSfile=JSPath, assetDelete=imgPath)