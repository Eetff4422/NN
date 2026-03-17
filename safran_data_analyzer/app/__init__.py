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

        from sqlalchemy import text
        from sqlalchemy.exc import OperationalError

        # Ajout manuel de la colonne 'anomaly_count' si elle manque dans une DB existante (migration brute)
        try:
            app.logger.info("Vérification de la présence de la colonne 'anomaly_count'...")
            db.session.execute(text("SELECT anomaly_count FROM report LIMIT 1"))
        except OperationalError as e:
            if "no such column" in str(e).lower():
                app.logger.warning("Colonne 'anomaly_count' manquante dans 'report'. Ajout de la colonne...")
                db.session.rollback() # Important: faire un rollback de l'erreur précédente
                try:
                    db.session.execute(text("ALTER TABLE report ADD COLUMN anomaly_count INTEGER DEFAULT 0"))
                    db.session.commit()
                    app.logger.info("Colonne 'anomaly_count' ajoutée avec succès.")
                except Exception as ex:
                    app.logger.error(f"Erreur lors de l'ajout de la colonne: {ex}")
                    db.session.rollback()
            else:
                 db.session.rollback() # Rollback si c'est une autre erreur

    return app