from app.config.database import Base
from app.models.userRoles_model import user_roles
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import validates
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

class User(Base):
    """Modelo de usuario."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    avatar_id = Column(Integer, ForeignKey("avatar_images.id"), nullable=True)
    is_active = Column(Boolean, default=True)

    # roles -> Lista de roles del usuario 
    roles = relationship("Role", secondary=user_roles, backref="users")
    avatar = relationship("AvatarImage", back_populates="users")
    
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
            "avatar": self.avatar.to_dict() if self.avatar else None,
            "roles": [role.to_dict()["name"] for role in self.roles]
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
