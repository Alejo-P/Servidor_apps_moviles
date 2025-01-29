import os
from flask import request, jsonify, Blueprint, send_from_directory
from config import settings as env

files_bp = Blueprint('files', __name__)

# Función para verificar la extensión del archivo
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in env.ALLOWED_EXTENSIONS

# Ruta para subir archivos
@files_bp.route("/upload", methods=["POST"]) # /api/v1/upload
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No hay campo de archivo"}), 400

    file = request.files['file']
    
    # Verificar el tamaño del archivo
    if file.content_length > env.MAX_CONTENT_LENGTH:
        return jsonify({"error": "El archivo excede el tamaño máximo permitido"}), 400

    if file.filename == '':
        return jsonify({"error": "Ningun archivo seleccionado"}), 400

    if file and allowed_file(file.filename):
        filename = file.filename
        
        # Comprobar si el archivo ya existe
        if os.path.exists(os.path.join(env.UPLOAD_FOLDER, filename)):
            return jsonify({"error": f"El archivo {filename} ya esta cargado"}), 400
        
        file.save(os.path.join(env.UPLOAD_FOLDER, filename))
        return jsonify({"message": "Archivo cargado exitosamente", "filename": filename}), 200

    return jsonify({"error": "La extension del archivo no esta permitida"}), 400

# Ruta para visualizar un PDF cargado
@files_bp.route("/pdf/<filename>", methods=["GET"])  # /api/v1/pdf/<filename>
def view_pdf(filename):
    # Ruta completa del archivo
    file_path = os.path.join(env.UPLOAD_FOLDER, filename)

    # Verificar si el archivo existe
    if not os.path.exists(file_path):
        return jsonify({"error": "Archivo no encontrado"}), 404

    # Enviar el archivo con los encabezados correctos
    return send_from_directory(
        env.UPLOAD_FOLDER,
        filename,
        mimetype="application/pdf",
        as_attachment=False  # Evita la descarga y permite la visualización en navegador
    )

# Ruta para listar los archivos subidos
@files_bp.route("/files", methods=["GET"]) # /api/v1/files
def list_files():
    # Listar archivos en la carpeta de subida
    files = os.listdir(env.UPLOAD_FOLDER)
    
    return jsonify({"files": files}), 200

# Ruta para eliminar un archivo
@files_bp.route("/delete/<filename>", methods=["DELETE"]) # /api/v1/delete/<filename>
def delete_file(filename):
    # Verificar si el archivo existe
    if not os.path.exists(os.path.join(env.UPLOAD_FOLDER, filename)):
        return jsonify({"error": "Archivo no encontrado"}), 404

    # Eliminar el archivo
    os.remove(os.path.join(env.UPLOAD_FOLDER, filename))
    
    return jsonify({"message": "Archivo eliminado exitosamente", "filename": filename}), 200