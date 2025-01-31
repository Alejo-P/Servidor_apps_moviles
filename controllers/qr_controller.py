import os
import qrcode
from flask import request, jsonify, Blueprint, send_from_directory, url_for
from config import settings as env

qr_bp = Blueprint('qrController', __name__)

# Ruta para generar un código QR (A partir de un texto)
@qr_bp.route("/qr", methods=["POST"])  # /api/v1/qr
def generate_qr():
    data = request.json or {} # Obtener los datos del cuerpo de la solicitud

    if 'text' not in data:
        return jsonify({"error": "No se proporciono el texto"}), 400

    text = data['text']

    # Crear el objeto QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    # Agregar los datos al objeto QR
    qr.add_data(text)
    qr.make(fit=True)

    # Crear la imagen del código QR
    img = qr.make_image(fill_color="black", back_color="white")

    # Nombre del archivo
    filename = f"{text}.png".replace(' ', '-').lower()

    # Guardar la imagen
    img.save(os.path.join(env.QR_FOLDER, filename))

    return jsonify({"message": "Código QR generado exitosamente", "filename": filename}), 200

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