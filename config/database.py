from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Inicializar la base de datos y crear todas las tablas
def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
        db.session.commit()
    