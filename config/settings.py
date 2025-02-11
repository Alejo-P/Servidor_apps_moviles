# Configuración del servidor
DEBUG = True
PORT = 5000
HOST = "0.0.0.0"

# Configuración de archivos
UPLOAD_FOLDER = './uploads'
STATIC_FOLDER = './static'
QR_FOLDER = './qrcode'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB