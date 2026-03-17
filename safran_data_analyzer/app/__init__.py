import os
from flask import Flask
from config import Config
from app.extensions import db, login_manager

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # 1. Initialisation de la base de données et du gestionnaire de connexion
    db.init_app(app)
    login_manager.init_app(app)
    
    # 2. Sécurité : Où renvoyer les gens qui ne sont pas connectés ?
    login_manager.login_view = 'login' 
    login_manager.login_message = "Veuillez vous authentifier pour accéder au tableau de bord."
    login_manager.login_message_category = "warning"

    with app.app_context():
        from . import routes
        from . import models # Obligatoire pour que SQLAlchemy crée les tables
        
        # 3. Création automatique des tables SQL si elles n'existent pas
        db.create_all()

    return app