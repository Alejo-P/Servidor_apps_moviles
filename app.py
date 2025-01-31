from flask import Flask, jsonify
from flask_cors import CORS
import os

# Importa controladores y vistas organizados en Blueprints
from controllers.files_controller import files_bp
from controllers.qr_controller import qr_bp
from views.files_view import upload_bp
from views.home_view import home_bp
from views.qr_view import qrview_bp
from config import settings as env

def create_app():
    """Función de fábrica para crear la aplicación Flask."""
    app = Flask(__name__)
    
    # Configuración del servidor
    app.config["UPLOAD_FOLDER"] = env.UPLOAD_FOLDER
    app.config["QR_FOLDER"] = env.QR_FOLDER
    app.config["ALLOWED_EXTENSIONS"] = env.ALLOWED_EXTENSIONS
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

    # Asegurar que la carpeta de subida y de QR existen
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["QR_FOLDER"], exist_ok=True)

    # Habilitar CORS (permite peticiones desde otros dominios)
    CORS(app)

    # Registrar Blueprints para organizar las rutas
    app.register_blueprint(home_bp, url_prefix="/")
    app.register_blueprint(files_bp, url_prefix="/api/v1")
    app.register_blueprint(qr_bp, url_prefix="/api/v1")
    app.register_blueprint(upload_bp, url_prefix="/views")
    app.register_blueprint(qrview_bp, url_prefix="/views")

    # Manejo de errores personalizados
    @app.errorhandler(404)
    def page_not_found(error):
        print(error)
        return jsonify({"error": "Ruta no encontrada"}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({"error": "Método no permitido"}), 405

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(
        host=env.HOST,
        port=env.PORT,
        debug=env.DEBUG
    )
