import os
import qrcode
import base64
from io import BytesIO
from flask import request, jsonify, Blueprint, send_from_directory, url_for
from PIL import Image
from config import settings as env

qr_bp = Blueprint('qrController', __name__)

# Ruta para generar un código QR con icono opcional
@qr_bp.route("/qr", methods=["POST"])
def generate_qr():
    # Detectar si la solicitud es JSON o multipart/form-data
    if request.content_type.startswith("application/json"):
        data = request.json or {}
        text = data.get('text')
        icon_base64 = data.get('icon')  # Icono en base64
        icon_img = decode_base64_icon(icon_base64) if icon_base64 else None
    elif request.content_type.startswith("multipart/form-data"):
        text = request.form.get('text')
        icon_file = request.files.get('icon')  # Icono como archivo binario
        icon_img = Image.open(icon_file) if icon_file else None
    else:
        return jsonify({"error": "Formato de solicitud no soportado"}), 400

    if not text:
        return jsonify({"error": "No se proporcionó el texto"}), 400

    filename = f"{text.replace(' ', '-').lower()}.png"
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

    return jsonify({"message": "Código QR generado exitosamente", "filename": filename}), 200

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
    icon_img = icon_img.resize((icon_size, icon_size), Image.ANTIALIAS)

    # Calcular la posición para centrar el icono
    icon_position = ((qr_size - icon_size) // 2, (qr_size - icon_size) // 2)

    # Pegar el icono sobre el QR
    qr_img.paste(icon_img, icon_position, mask=icon_img if icon_img.mode == "RGBA" else None)

    return qr_img


# Ruta para generar un código QR (A partir de un archivo)
@qr_bp.route("/qr/file/<filename>", methods=["GET"])  # /api/v1/qr/file/<filename>
def generate_qr_from_file(filename):
    # Verificar si el archivo existe
    if not os.path.exists(os.path.join(env.UPLOAD_FOLDER, filename)):
        return jsonify({"error": "Archivo no encontrado"}), 404

    # Si ya existe un QR, devolver una solicitud exitosa
    qr_path = os.path.join(env.QR_FOLDER, f"{filename}.png")
    if os.path.exists(qr_path):
        return jsonify({"message": "Código QR ya generado", "filename": f"{filename}.png"}), 200

    # Construye la URL de acceso al archivo
    file_url = url_for('filesController.view_file', filename=filename, _external=True)

    # Genera el código QR
    qr = qrcode.make(file_url)

    # Nombre del archivo
    qr_filename = f"{filename}.png".replace(' ', '-').lower()

    # Guardar la imagen
    qr.save(os.path.join(env.QR_FOLDER, qr_filename))

    return jsonify({"message": "Código QR generado exitosamente", "filename": qr_filename}), 200

# Ruta para visualizar un código QR
@qr_bp.route("/qr/<filename>", methods=["GET"])
def view_qr(filename):
    # Convertimos el nombre a minúsculas para evitar problemas de coincidencia
    filename = filename.lower()
    file_path = os.path.join(env.QR_FOLDER, filename)

    if not os.path.exists(file_path):
        return jsonify({"error": "QR no encontrado"}), 404

    # Servir el archivo desde la carpeta correcta
    return send_from_directory(env.QR_FOLDER, filename, mimetype='image/png')

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

# Ruta para listar los códigos QR generados
@qr_bp.route("/qrs", methods=["GET"])  # /api/v1/qrs
def list_qrs():
    # Listar archivos en la carpeta de códigos QR
    files = os.listdir(env.QR_FOLDER)

    return jsonify({"files": files}), 200

# Ruta para eliminar un código QR
@qr_bp.route("/qr/<filename>", methods=["DELETE"])  # /api/v1/qr/<filename>
def delete_qr(filename):
    # Verificar si el archivo existe
    if not os.path.exists(os.path.join(env.QR_FOLDER, filename)):
        return jsonify({"error": "Archivo no encontrado"}), 404

    # Eliminar el archivo
    os.remove(os.path.join(env.QR_FOLDER, filename))

    return jsonify({"message": "Código QR eliminado exitosamente", "filename": filename}), 200

# Ruta para eliminar todos los códigos QR
@qr_bp.route("/qrs", methods=["DELETE"])  # /api/v1/qrs
def delete_all_qrs():
    # Listar archivos en la carpeta de códigos QR
    files = os.listdir(env.QR_FOLDER)

    # Eliminar los códigos QR
    for file in files:
        os.remove(os.path.join(env.QR_FOLDER, file))

    return jsonify({"message": "Códigos QR eliminados exitosamente"}), 200