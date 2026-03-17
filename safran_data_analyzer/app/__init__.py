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
        from sqlalchemy.exc import OperationalError
        try:
            # On vérifie si la colonne anomaly_count existe, si elle n'existe pas, on modifie ou on drop la DB
            app.logger.info("Vérification des tables de la base de données...")
            models.Report.query.limit(1).all()
        except OperationalError as e:
            if "no such column: report.anomaly_count" in str(e):
                app.logger.warning("La colonne 'anomaly_count' est manquante. Suppression et recréation de la base de données pour appliquer la mise à jour...")
                db.drop_all()
        db.create_all()

    return app