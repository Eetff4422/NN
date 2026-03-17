import os
from datetime import timedelta

class Config:
    """Configuration globale de l'application."""
    # Clé secrète pour les sessions Flask
    SECRET_KEY = "safran_tech_dir_secret"
    
    # Chemin absolu vers le dossier d'upload
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    
    # Limite de poids du fichier conservée (16 Mo)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    # Extensions autorisées (facile à modifier plus tard)
    ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

    # NOUVEAU : Configuration de la base de données SQLite
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'safran.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # NOUVEAU : Expiration de la session après 15 minutes d'inactivité
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=15)

    # NOUVEAU : Domaines e-mail autorisés pour l'inscription (Configuration Générique)
    ALLOWED_DOMAINS = ['@safrangroup.com', '@safran.fr']