from flask import render_template, Blueprint, send_from_directory, jsonify, url_for
from config import settings as env
import os

upload_bp = Blueprint('upload', __name__)

@upload_bp.route("/upload", methods=["GET"]) # /views/upload
def upload_form():
    files_ext =", ".join(env.ALLOWED_EXTENSIONS) # Unir las extensiones permitidas
    return render_template('uploadForm.html', extensions=files_ext)

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
        detail = {
            "name": f,
            "qr": f""
        }
        if f"QR-{f}.png" in qr_files:
            detail["qr"] = f"{env.HOST}:{env.PORT}{url_for('files.view_pdf', filename=f, _external=True)}"
        outputFile.append(detail)
    
    return render_template("viewPDFs.html", files=outputFile)