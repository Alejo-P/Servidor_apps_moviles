from flask import render_template, Blueprint, send_from_directory, jsonify
from config import settings as env
import os

upload_bp = Blueprint('upload', __name__)

@upload_bp.route("/upload", methods=["GET"]) # /views/upload
def upload_form():
    # Servir el archivo HTML del formulario de subida (ubicado en /static/html/uploadForm.html)
    print('uploadForm.html')
    
    return render_template('uploadForm.html')

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
    
    return render_template("viewPDFs.html", files=files)