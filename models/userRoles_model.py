from config.database import db
from sqlalchemy import Column, Integer, ForeignKey

user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True)
)

#TODO: Definir un rol principal para cada usuario, por ejemplo, "Usuario" o "Admin".