from flask import Flask, jsonify
from datetime import timedelta
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Importa controladores y vistas organizados en Blueprints
from controllers.files_controller import files_bp
from controllers.qr_controller import qr_bp
from controllers.auth_controller import auth_bp
from views.files_view import upload_bp
from views.home_view import home_bp
from views.qr_view import qrview_bp
from config import settings as env

# Importa la base de datos
from config.database import db

# Cargar variables de entorno desde el archivo .env
load_dotenv()
jwt = JWTManager()

def create_app():
    """Función de fábrica para crear la aplicación Flask."""
    app = Flask(__name__)
    
    # Configuración del servidor
    app.config["UPLOAD_FOLDER"] = env.UPLOAD_FOLDER
    app.config["QR_FOLDER"] = env.QR_FOLDER
    app.config["ALLOWED_EXTENSIONS"] = env.ALLOWED_EXTENSIONS
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB
    
    # Configuración de la base de datos
    app.config["SQLALCHEMY_DATABASE_URI"] = env.SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = env.SQLALCHEMY_TRACK_MODIFICATIONS
    
    # Configuración del JWT
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_IN")))
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_IN")))

    # Asegurar que la carpeta de subida y de QR existen
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["QR_FOLDER"], exist_ok=True)

    # Habilitar CORS (permite peticiones desde otros dominios)
    CORS(app)
    
    # Inicializar la base de datos
    db.init_app(app)
    
    # Inicializar el JWT
    jwt.init_app(app)

    # Registrar Blueprints para organizar las rutas
    app.register_blueprint(home_bp, url_prefix="/")
    app.register_blueprint(files_bp, url_prefix="/api/v1")
    app.register_blueprint(qr_bp, url_prefix="/api/v1")
    app.register_blueprint(auth_bp, url_prefix="/api/v1")
    app.register_blueprint(upload_bp, url_prefix="/views")
    app.register_blueprint(qrview_bp, url_prefix="/views")

    # Manejo de errores personalizados
    @app.errorhandler(404)
    def page_not_found(error):
        print(error)
        return jsonify({"error": "Ruta no encontrada"}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({"error": "Método no permitido", "message":str(error)}), 405

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(
        host=env.HOST,
        port=env.PORT,
        debug=env.DEBUG
    )
