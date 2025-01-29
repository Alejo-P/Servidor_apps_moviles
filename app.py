from flask import Flask, jsonify
from flask_cors import CORS
import os

# Importa controladores y vistas organizados en Blueprints
from controllers.example_controller import example_bp
from controllers.files_controller import files_bp
from views.files_view import upload_bp
from config import settings as env

def create_app():
    """Función de fábrica para crear la aplicación Flask."""
    app = Flask(__name__)
    
    # Configuración del servidor
    app.config["UPLOAD_FOLDER"] = env.UPLOAD_FOLDER
    app.config["ALLOWED_EXTENSIONS"] = env.ALLOWED_EXTENSIONS
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

    # Asegurar que la carpeta de subida existe
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Habilitar CORS (permite peticiones desde otros dominios)
    CORS(app)

    # Registrar Blueprints para organizar las rutas
    app.register_blueprint(example_bp, url_prefix="/api/v1")
    app.register_blueprint(files_bp, url_prefix="/api/v1")
    app.register_blueprint(upload_bp, url_prefix="/views")
    
    # Ruta principal de la API
    @app.route("/", methods=["GET"])
    def index():
        return jsonify({"message": "Bienvenido a la API"}), 200

    # Manejo de errores personalizados
    @app.errorhandler(404)
    def page_not_found(error):
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
