import os, uuid
from flask import request, jsonify, Blueprint, send_from_directory, url_for
from config import settings as env
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from werkzeug.utils import secure_filename

# Importar la base de datos
from config.database import db
from models.files_model import File
from models.qr_model import QRCode

# Crear un Blueprint
files_bp = Blueprint('filesController', __name__)

# Función para verificar la extensión del archivo
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in env.ALLOWED_EXTENSIONS

# Función para generar un nombre único
def get_unique_filename(filename):
    """Genera un nombre único para evitar conflictos."""
    name, ext = os.path.splitext(filename)
    return f"{name}_{uuid.uuid4().hex[:8]}{ext}"

# Ruta para subir archivos
@files_bp.route("/upload", methods=["POST"]) # /api/v1/upload
@jwt_required()
def upload_file():
    user_id = get_jwt_identity()
    if user_id is None:
        return jsonify({"error": "Usuario no autenticado"}), 401
    
    print(request.files)
    
    # Verificar si se envió un archivo
    if 'file' not in request.files:
        return jsonify({"error": "No hay campo de archivo"}), 400

    file = request.files['file']
    
    file_size = os.fstat(file.fileno()).st_size
    if file_size > env.MAX_CONTENT_LENGTH:
        return jsonify({"error": "El archivo excede el tamaño máximo permitido"}), 400

    if file.filename == '':
        return jsonify({"error": "Ningun archivo seleccionado"}), 400

    if file and allowed_file(file.filename):
        #filename = file.filename.replace(' ', '-').lower()
        filename = secure_filename(file.filename)
        
        # Comprobar si el archivo ya existe
        if os.path.exists(os.path.join(env.UPLOAD_FOLDER, filename)):
            filename = get_unique_filename(filename)
            
        file.save(os.path.join(env.UPLOAD_FOLDER, filename))
        
        new_file = File(
            filename=filename,
            filepath=os.path.join(env.UPLOAD_FOLDER, filename),
            file_size=file_size,
            file_type=file.content_type if file.content_type else "application/octet-stream",
            uploaded_by=user_id
        )

        db.session.add(new_file)
        db.session.commit()

        return jsonify({
            "msg": "Archivo cargado exitosamente",
            "filename": filename,
            "file_id": new_file.id
        }), 201


    return jsonify({"error": "La extension del archivo no esta permitida"}), 400

# Ruta para obtener un archivo cargado
@files_bp.route("/file/<filename>", methods=["GET"]) # /api/v1/file/<filename>
def get_file(filename):
    # Ruta completa del archivo
    file_path = os.path.join(env.UPLOAD_FOLDER, filename)

    # Verificar si el archivo existe
    if not os.path.exists(file_path):
        return jsonify({"error": "Archivo no encontrado"}), 404

    # Servir la URL de acceso al archivo
    return jsonify({"url": url_for('filesController.view_file', filename=filename, _external=True), "filename": filename}), 200

# Ruta para descargar un archivo cargado
@files_bp.route("/download/file/<filename>", methods=["GET"])  # /api/v1/download/<filename>
def download_file(filename):
    # Ruta completa del archivo
    file_path = os.path.join(env.UPLOAD_FOLDER, filename)
    
    # Verificar si el archivo existe
    if not os.path.exists(file_path):
        return jsonify({"error": "Archivo no encontrado"}), 404

    # Enviar el archivo con los encabezados correctos
    return send_from_directory(env.UPLOAD_FOLDER, filename, as_attachment=True)

# Ruta para visualizar un archivo cargado
@files_bp.route("/view/file/<filename>", methods=["GET"])  # /api/v1/file/<filename>
def view_file(filename):
    # Ruta completa del archivo
    file_path = os.path.join(env.UPLOAD_FOLDER, filename)

    # Verificar si el archivo existe
    if not os.path.exists(file_path):
        return jsonify({"error": "Archivo no encontrado"}), 404

    # Enviar el archivo con los encabezados correctos
    return send_from_directory(env.UPLOAD_FOLDER, filename)

# Ruta para listar los archivos subidos
@files_bp.route("/files", methods=["GET"]) # /api/v1/files
@jwt_required()
def list_files():
    user_id = get_jwt_identity()
    claims = get_jwt()
    
    if user_id is None:
        return jsonify({"error": "Usuario no autenticado"}), 401
    
    user_role = claims.get("role")
    if user_role != "admin":
        files_records = File.query.filter_by(uploaded_by=user_id).all()
    else:
        files_records = File.query.all()
        
    files = []
    for archivo in files_records:
        if not os.path.exists(archivo.filepath): # Verificar si el archivo existe
            db.session.delete(archivo)
            db.session.commit()
            continue
        
        files.append(archivo.filename)
    
    if not files:
        return jsonify({"error": "No hay archivos disponibles"}), 404
    
    return jsonify({"files": files}), 200

# Ruta para eliminar un archivo
@files_bp.route("/delete/file/<filename>", methods=["DELETE"]) # /api/v1/delete/file/<filename>
@jwt_required()
def delete_file(filename):
    user_id = get_jwt_identity()
    if user_id is None:
        return jsonify({"error": "Usuario no autenticado"}), 401
    
    claims = get_jwt()
    user_role = claims.get("role")
    
    if user_role != "admin":
        file_record = File.query.filter_by(
            filename=filename,
            uploaded_by=user_id
        ).first()
    else:
        file_record = File.query.filter_by(filename=filename).first()
    
    if not file_record:
        return jsonify({"error": "Archivo no encontrado"}), 404

    # Eliminar el archivo físico
    file_path = file_record.filepath
    if os.path.exists(file_path):
        os.remove(file_path)

    # Eliminar QR si existe
    id_qr = file_record.qr_code
    if id_qr:
        qr_record = QRCode.query.get(id_qr)
        if qr_record:
            qr_path = qr_record.filename
            if os.path.exists(qr_path):
                os.remove(qr_path)
            db.session.delete(qr_record)
            db.session.commit()

    # Eliminar registro de la BD
    db.session.delete(file_record)
    db.session.commit()

    return jsonify({"msg": "Archivo eliminado exitosamente"}), 200

# Ruta para eliminar todos los archivos
@files_bp.route("/delete/all", methods=["DELETE"]) # /api/v1/delete/all
@jwt_required()
def delete_all_files():
    user_id = get_jwt_identity()
    if user_id is None:
        return jsonify({"error": "Usuario no autenticado"}), 401
    
    claims = get_jwt()
    user_role = claims.get("role")
    
    if user_role != "admin":
        files_records = File.query.filter_by(uploaded_by=user_id).all()
    else:
        files_records = File.query.all()
    
    # Eliminar archivos en la carpeta de subida
    files = []
    for archivo in files_records:
        if not os.path.exists(archivo.filepath):
            db.session.delete(archivo)
            db.session.commit()
            continue
        
        id_qr = archivo.qr_code
        if id_qr:
            qr_record = QRCode.query.get(id_qr)
            if qr_record:
                qr_path = qr_record.filename
                if os.path.exists(qr_path):
                    os.remove(qr_path)
                db.session.delete(qr_record)
                db.session.commit()
        
        files.append(archivo.filename)
        os.remove(archivo.filepath)
        db.session.delete(archivo)
        db.session.commit()
        
        
    if not files:
        return jsonify({"error": "No hay archivos disponibles"}), 404
    
    # Eliminar archivos
    for file in files:
        os.remove(os.path.join(env.UPLOAD_FOLDER, file))
        
        # Verificar si existe un QR asociado
        file_record = File.query.filter_by(filename=file).first()
        if file_record:
            id_qr = file_record.qr_code
            if id_qr:
                qr_record = QRCode.query.get(id_qr)
                if qr_record:
                    qr_path = qr_record.filename
                    if os.path.exists(qr_path):
                        os.remove(qr_path)
                    db.session.delete(qr_record)
                    db.session.commit()
            
        # Eliminar registro de la BD
        file_record = File.query.filter_by(filename=file).first()
        if file_record:
            db.session.delete(file_record)
            db.session.commit()
    
    return jsonify({"msg": "Archivos eliminados exitosamente"}), 200