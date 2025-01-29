import os
from flask import request, jsonify, Blueprint, send_from_directory
from config import settings as env

files_bp = Blueprint('files', __name__)

# Función para verificar la extensión del archivo
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in env.ALLOWED_EXTENSIONS

# Ruta para subir archivos
@files_bp.route("/upload", methods=["POST"])  # ✅ Ahora sí es un decorador
def upload_file():
    print(request)
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = file.filename
        file.save(os.path.join(env.UPLOAD_FOLDER, filename))
        return jsonify({"message": "File uploaded successfully", "filename": filename}), 200

    return jsonify({"error": "File type not allowed"}), 400

# Ruta para visualizar un PDF cargado
@files_bp.route("/pdf/<filename>", methods=["GET"]) # /views/pdf/<filename>
def view_pdf(filename):
    # Verificar si el archivo existe
    if not os.path.exists(os.path.join(env.UPLOAD_FOLDER, filename)):
        return jsonify({"error": "File not found"}), 404

    # Servir el archivo PDF
    return send_from_directory(env.UPLOAD_FOLDER, filename)

# Ruta para listar los archivos subidos
@files_bp.route("/files", methods=["GET"]) # /views/files
def list_files():
    # Listar archivos en la carpeta de subida
    files = os.listdir(env.UPLOAD_FOLDER)
    
    return jsonify({"files": files}), 200