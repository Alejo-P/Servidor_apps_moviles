from config.database import db
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import validates
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """Modelo de usuario."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    role = Column(String(50), default="user")
    
    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password
    
    def __repr__(self):
        return f"<User {self.name}>"
    
    @validates("password")
    def validate_password(self, key, password):
        """Valida la contraseña y la hashea."""
        if len(password) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        
        if not any(char.isdigit() for char in password):
            raise ValueError("La contraseña debe contener al menos un número.")
        
        return generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica que la contraseña sea correcta."""
        return check_password_hash(self.password, password)
    
    def to_dict(self):
        """Devuelve un diccionario con los datos del usuario."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email
        }
