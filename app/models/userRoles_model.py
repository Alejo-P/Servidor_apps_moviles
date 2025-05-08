from sqlalchemy import Table, Column, Integer, ForeignKey
from app.config.database import Base

user_roles = Table(
    "user_roles",
    Base.metadata,  # Usa Base.metadata para registrar la tabla
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True)
)