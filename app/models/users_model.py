from app.config.database import Base
from app.models.userRoles_model import user_roles
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import validates, relationship
from werkzeug.security import generate_password_hash, check_password_hash

class User(Base):
    """Modelo de usuario."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    avatar_id = Column(Integer, ForeignKey("avatar_images.id"), nullable=True)
    token = Column(String(255), nullable=True, unique=True, default=None)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_connected = Column(Boolean, default=False) # Indica si el usuario está conectado

    # roles -> Lista de roles del usuario 
    roles = relationship("Role", secondary=user_roles, backref="users")
    avatar = relationship("AvatarImage", back_populates="users")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    actions = relationship("UserAction", back_populates="user", cascade="all, delete-orphan")
    
    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password
    
    def __repr__(self):
        return f"<User {self.name}>"
    
    def to_dict(self):
        """Devuelve un diccionario con los datos del usuario."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_connected": self.is_connected,
            "avatar": self.avatar.to_dict() if self.avatar else None,
            "roles": [role.to_dict()["name"] for role in self.roles],
            "actions": [action.to_dict() for action in self.actions]
        }
    
    def check_password(self, password):
        """Verifica que la contraseña sea correcta."""
        return check_password_hash(self.password, password)
    
    @validates("password")
    def validate_password(self, key, password):
        """Valida la contraseña y la hashea."""
        if len(password) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        
        if not any(char.isdigit() for char in password):
            raise ValueError("La contraseña debe contener al menos un número.")
        
        return generate_password_hash(password)
