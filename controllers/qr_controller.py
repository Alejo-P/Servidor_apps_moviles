import os
import qrcode
import base64
from io import BytesIO
from flask import request, jsonify, Blueprint, send_from_directory, url_for
from PIL import Image
from config import settings as env
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from werkzeug.utils import secure_filename

# Importar la base de datos
from config.database import db
from models.qr_model import QRCode
from models.files_model import File

qr_bp = Blueprint('qrController', __name__)

# Ruta para generar un código QR con icono opcional
@qr_bp.route("/qr", methods=["POST"])
@jwt_required()
def generate_qr():
    name = None
    name_file = None
    text = None
    icon_base64 = None
    icon_img = None
    
    user_id = get_jwt_identity()
    if user_id is None:
        return jsonify({"error": "Usuario no autenticado"}), 401
    
    try:
        # Detectar si la solicitud es JSON o multipart/form-data
        if request.content_type.startswith("application/json"):
            data = request.json or {}
            name = data.get('name')
            text = data.get('text')
            icon_base64 = data.get('icon')  # Icono en base64
            icon_img = decode_base64_icon(icon_base64) if icon_base64 else None
        elif request.content_type.startswith("multipart/form-data"):
            text = request.form.get('text')
            icon_file = request.files.get('icon')  # Icono como archivo binario
            name_file = request.form.get('name')  # Nombre del archivo
            icon_img = Image.open(icon_file) if icon_file else None
        else:
            return jsonify({"error": "Formato de solicitud no soportado"}), 400

        if not text:
            return jsonify({"error": "No se proporcionó el texto"}), 400
        
        # Si se proporciona un nombre, se usa ese nombre para el archivo
        if name:
            filename = f"{secure_filename(name)}.png"
        elif name_file:
            filename = f"{secure_filename(name_file)}.png"
        else:
            filename = f"{secure_filename(text)}.png"
                
        qr_path = os.path.join(env.QR_FOLDER, filename)

        # Comprobar si el QR ya existe
        if os.path.exists(qr_path):
            return jsonify({"error": "QR para ese texto ya generado"}), 400
    
        # Crear el objeto QR con alta corrección de errores
        qr = qrcode.QRCode(
            version=5,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )

        qr.add_data(text)
        qr.make(fit=True)

        # Generar imagen del código QR
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")

        # 📌 Si hay un icono, agregarlo en el centro
        if icon_img:
            qr_img = add_icon_to_qr(qr_img, icon_img)

        # Guardar el QR con icono
        qr_img.save(qr_path)
        
        # Guardar en la base de datos
        qr_entry = QRCode(
            filename=filename,
            text=text,
            filepath=qr_path,
            created_by=user_id
        )
        db.session.add(qr_entry)
        db.session.commit()

        return jsonify({"msg": "Código QR generado exitosamente", "filename": filename}), 200
    except:
        return jsonify({"msg": "Error al generar el código QR"}), 500

# Función para decodificar un icono en base64
def decode_base64_icon(icon_base64):
    try:
        icon_data = base64.b64decode(icon_base64)
        return Image.open(BytesIO(icon_data))
    except Exception as e:
        print(f"Error decodificando icono: {e}")
        return None  # Si hay error, retorna None y se genera el QR sin icono

# Función para agregar un icono en el centro del QR
def add_icon_to_qr(qr_img, icon_img):
    qr_size = qr_img.size[0]
    icon_size = qr_size // 4  # Ajustar tamaño del icono
    icon_img = icon_img.resize((icon_size, icon_size), Image.Resampling.BOX)

    # Calcular la posición para centrar el icono
    icon_position = ((qr_size - icon_size) // 2, (qr_size - icon_size) // 2)

    # Pegar el icono sobre el QR
    qr_img.paste(icon_img, icon_position, mask=icon_img if icon_img.mode == "RGBA" else None)

    return qr_img


# Ruta para generar un código QR (A partir de un archivo)
@qr_bp.route("/qr/file/<filename>", methods=["POST"])  # /api/v1/qr/file/<filename>
@jwt_required()
def generate_qr_from_file(filename):
    user_id = get_jwt_identity()
    if user_id is None:
        return jsonify({"error": "Usuario no autenticado"}), 401
    
    # Verificar si el archivo existe
    if not os.path.exists(os.path.join(env.UPLOAD_FOLDER, filename)):
        return jsonify({"error": "Archivo no encontrado"}), 404

    # Si ya existe un QR, devolver una solicitud exitosa
    qr_path = os.path.join(env.QR_FOLDER, f"{filename}.png")
    if os.path.exists(qr_path):
        return jsonify({"msg": "Código QR ya generado", "filename": f"{filename}.png"}), 200
    
    try:
        # Construye la URL de acceso al archivo
        file_url = url_for('filesController.view_file', filename=filename, _external=True)

        # Genera el código QR
        qr = qrcode.make(file_url)

        # Nombre del archivo
        qr_filename = f"{filename}.png"

        # Guardar la imagen
        qr.save(os.path.join(env.QR_FOLDER, qr_filename))
        
        # Guardar en la base de datos
        qr_entry = QRCode(
            filename=qr_filename,
            text=file_url,
            filepath=os.path.join(env.QR_FOLDER, qr_filename),
            created_by=user_id
        )
        db.session.add(qr_entry)
        db.session.commit()
        
        # Guardar en la base de datos la id del qr generado
        file_record = File.query.filter_by(filename=filename).first()
        if not file_record:
            return jsonify({"error": f"El archivo '{filename}' no fue encontrado en la base de datos"}), 404
            
        file_record.qr_code = qr_entry.id
        db.session.commit()

        return jsonify({"msg": "Código QR generado exitosamente", "filename": qr_filename}), 200
    except Exception as e:
        print(f"Error generando QR: {e}")
        
        for clave, valor in e.__dict__.items():
            print(f"{clave}: {valor}")
        
        return jsonify({"msg": "Error al generar el código QR", "error":str(e)}), 500

# Ruta para obtener un código QR
@qr_bp.route("/qr/<filename>", methods=["GET"]) # /api/v1/qr/<filename>
@jwt_required()
def view_qr(filename):
    user_id = get_jwt_identity()
    if user_id is None:
        return jsonify({"error": "Usuario no autenticado"}),
    
    claims = get_jwt()
    if not claims:
        return jsonify({"error": "Token inválido"}), 400
    
    user_role = claims.get("role")
    if user_role != "admin":
        qr_record = QRCode.query.filter_by(filename=filename, created_by=user_id).first()
    else:
        qr_record = QRCode.query.filter_by(filename=filename).first()
    
    if not qr_record:
        return jsonify({"error": "QR no encontrado"}), 404
    
    file_path = qr_record.filepath
    if not os.path.exists(file_path):
        return jsonify({"error": "QR no encontrado"}), 404

    # Servir la URL de acceso al archivo
    return jsonify({"url": url_for('qrController.view_qr_image', filename=filename, _external=True), "filename": filename}), 200 # /api/v1/view/qr/<filename>

# Ruta para descargar un código QR
@qr_bp.route("/download/qr/<filename>", methods=["GET"])  # /api/v1/download/qr/<filename>
def download_qr(filename):
    # Convertimos el nombre a minúsculas para evitar problemas de coincidencia
    filename = filename.lower()
    file_path = os.path.join(env.QR_FOLDER, filename)

    if not os.path.exists(file_path):
        return jsonify({"error": "QR no encontrado"}), 404

    # Enviar el archivo con los encabezados correctos
    return send_from_directory(env.QR_FOLDER, filename, as_attachment=True, mimetype='image/png')

# Ruta para visualizar un código QR
@qr_bp.route("/view/qr/<filename>", methods=["GET"])  # /api/v1/view/qr/<filename>
def view_qr_image(filename):
    # Convertimos el nombre a minúsculas para evitar problemas de coincidencia
    filename = filename.lower()
    file_path = os.path.join(env.QR_FOLDER, filename)

    if not os.path.exists(file_path):
        return jsonify({"error": "QR no encontrado"}), 404

    # Servir la imagen del código QR
    return send_from_directory(env.QR_FOLDER, filename, mimetype='image/png')

# Ruta para listar los códigos QR generados
@qr_bp.route("/qrs", methods=["GET"])  # /api/v1/qrs
@jwt_required()
def list_qrs():
    user_id = get_jwt_identity()
    if user_id is None:
        return jsonify({"error": "Usuario no autenticado"}), 401
    
    claims = get_jwt()
    if not claims:
        return jsonify({"error": "Token inválido"}), 400
    
    user_role = claims.get("role")
    if user_role != "admin":
        qr_records = QRCode.query.filter_by(created_by=user_id).all()
    else:
        qr_records = QRCode.query.all()
    
    # Listar archivos en la carpeta de códigos QR
    files = []
    for qr in qr_records:
        if not os.path.exists(qr.filepath): # Verificar si el archivo existe
            db.session.delete(qr)
            db.session.commit()
            continue
        
        files.append(qr.filename)
    
    if not files:
        return jsonify({"msg": "No hay códigos QR generados"}), 404

    return jsonify({"files": files}), 200

# Ruta para eliminar un código QR
@qr_bp.route("/qr/<filename>", methods=["DELETE"])  # /api/v1/qr/<filename>
@jwt_required()
def delete_qr(filename):
    user_id = get_jwt_identity()
    if user_id is None:
        return jsonify({"error": "Usuario no autenticado"}), 401
    
    # Verificar si el archivo existe
    if not os.path.exists(os.path.join(env.QR_FOLDER, filename)):
        return jsonify({"error": "Archivo no encontrado"}), 404

    # Eliminar el archivo
    os.remove(os.path.join(env.QR_FOLDER, filename))
    
    # Eliminar el registro de la base de datos
    qr_entry = QRCode.query.filter_by(filename=filename).first()
    file_record = File.query.filter_by(qr_code=qr_entry.id).first()
    if file_record:
        file_record.qr_code = None
        db.session.commit()
    
    if qr_entry:
        db.session.delete(qr_entry)
        db.session.commit()

    return jsonify({"msg": "Código QR eliminado exitosamente", "filename": filename}), 200

# Ruta para eliminar todos los códigos QR
@qr_bp.route("/qrs", methods=["DELETE"])  # /api/v1/qrs
@jwt_required()
def delete_all_qrs():
    user_id = get_jwt_identity()
    if user_id is None:
        return jsonify({"error": "Usuario no autenticado"}), 401
    
    # Listar archivos en la carpeta de códigos QR
    files = os.listdir(env.QR_FOLDER)

    # Eliminar los códigos QR
    for file in files:
        os.remove(os.path.join(env.QR_FOLDER, file))
        
        # Eliminar el registro de la base de datos
        qr_entry = QRCode.query.filter_by(filename=file).first()
        file_record = File.query.filter_by(qr_code=qr_entry.id).first()
        if file_record:
            file_record.qr_code = None
            db.session.commit()
        
        if qr_entry:
            db.session.delete(qr_entry)
            db.session.commit()

    return jsonify({"msg": "Códigos QR eliminados exitosamente"}), 200