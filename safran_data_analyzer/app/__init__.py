"""Initialisation de l'application Flask et configuration."""
import os
from flask import Flask
from config import Config
from app.extensions import db, login_manager

def create_app():
    """Application Factory pattern."""
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['BASE_DIR'], '../data'), exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    
    login_manager.login_view = 'login' 
    login_manager.login_message = "Veuillez vous authentifier pour accéder au tableau de bord."
    login_manager.login_message_category = "warning"

    with app.app_context():
        from . import routes
        from . import models
        db.create_all()

    return app