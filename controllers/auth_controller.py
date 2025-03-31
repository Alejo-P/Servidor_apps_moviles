from datetime import datetime
from flask import request, jsonify, Blueprint, send_from_directory, url_for
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt, jwt_required, get_jwt_identity
from models.users_model import User
from models.roles_model import Role
from models.token_model import RefreshToken
from config.database import db

auth_bp = Blueprint('authController', __name__)

def register_user(name, email, password):
    """Registra un nuevo usuario en la base de datos."""
    user = User(name=name, email=email, password=password)
    user_role = Role.query.filter_by(name="Usuario").first()
    user.roles.append(user_role)
    
    # Guardar el usuario en la base de datos
    db.session.add(user)
    db.session.commit()
    return jsonify({"msg": "Usuario registrado exitosamente"})

@auth_bp.route("/register", methods=["POST"])  # /api/v1/register
def register():
    """Registra un nuevo usuario."""
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    
    if not name or not email or not password:
        return jsonify({"error": "Faltan datos"}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "El email ya está registrado"}), 400
    
    response = register_user(name, email, password)
    return jsonify(response), 201

@auth_bp.route("/login", methods=["POST"])  # /api/v1/login
def login():
    """Inicia sesión de un usuario."""
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"error": "Faltan datos"}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        return jsonify({"error": "Email o contraseña incorrectos"}), 400
    
    aditional_claims = {
        "roles": user.roles
    }
    
    access_token = create_access_token(identity=str(user.id), additional_claims=aditional_claims)
    refresh_token = create_refresh_token(identity=str(user.id))
    
    # Guardar el token de refresco en la base de datos
    token = RefreshToken(token=refresh_token, user_id=user.id)
    db.session.add(token)
    db.session.commit()
    return jsonify({"access_token": access_token, "refresh_token": refresh_token}), 200

@auth_bp.route("/refresh", methods=["POST"])  # /api/v1/refresh
def refresh():
    """Refresca el token de acceso."""
    refresh_token = request.get_json().get("refresh_token")
    
    if not refresh_token:
        return jsonify({"error": "Falta el token de refresco"}), 400
    
    token = RefreshToken.query.filter_by(token=refresh_token, is_active=True).first()
    
    if not token:
        return jsonify({"error": "Token de refresco inválido"}), 400
    
    user_record = User.query.get(token.user_id)
    if not user_record:
        return jsonify({"error": "Usuario no encontrado"}), 404
    
    additional_claims = {
        "roles": user_record.roles
    }
    
    access_token = create_access_token(identity=token.user_id, additional_claims=additional_claims)
    # Actualizar el token de refresco en la base de datos
    return jsonify({"access_token": access_token, "refresh_token": refresh_token}), 200

@auth_bp.route("/active_sessions", methods=["POST"])  # /api/v1/active_sessions
@jwt_required()
def active_sessions():
    """Devuelve las sesiones activas de un usuario."""
    user_id = get_jwt_identity()
    tokens = RefreshToken.query.filter_by(
        RefreshToken.user_id == user_id,
        RefreshToken.is_active == True,
        RefreshToken.expires_at > datetime.utcnow()
    ).all()
    
    return jsonify([token.to_dict() for token in tokens]), 200

@auth_bp.route("/logout", methods=["POST"])  # /api/v1/logout
@jwt_required()
def logout():
    """Cierra la sesión de un usuario."""
    user_id = get_jwt_identity()
    token = RefreshToken.query.filter_by(
        user_id = user_id,
        is_active = True,
    ).first()
    if not token:
        return jsonify({"error": "No hay sesión activa"}), 400
    
    db.session.delete(token)
    db.session.commit()
    return jsonify({"msg": "Sesión cerrada exitosamente"}), 200

@auth_bp.route("/profile", methods=["GET"])  # /api/v1/profile
@jwt_required()
def profile():
    """Devuelve los datos del usuario."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return jsonify(user.to_dict()), 200

@auth_bp.route("/profile/<int:user_id>", methods=["GET"])  # /api/v1/profile/<user_id>
@jwt_required()
def get_user_profile(user_id):
    """Devuelve los datos de un usuario."""
    userAuth_id = get_jwt_identity()
    if not userAuth_id:
        return jsonify({"error": "Usuario no autenticado"}), 401
    
    claims = get_jwt()
    user_role = claims.get("role")
    if user_role != "admin":
        return jsonify({"error": "No tienes permisos para acceder a este recurso"}), 403
    
    # Verificar si el usuario existe
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    
    return jsonify(user.to_dict()), 200 