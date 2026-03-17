import os
from datetime import timedelta

class Config:
    """Configuration centralisée de l'application Safran Data Analyzer."""
    
    SECRET_KEY = os.environ.get("SECRET_KEY", "safran_tech_dir_secret")
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    
    # Stockage fichiers : répertoire uploads/, 10 Mo max
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    
    # Extensions autorisées
    ALLOWED_EXTENSIONS = {'xlsx'}

    # Base de données : SQLite en dev (data/app.db), PostgreSQL en prod (DATABASE_URL)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(BASE_DIR, '../data/app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session : expiration 15 min
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=15)

    # Domaines autorisés dans config.py
    ALLOWED_DOMAINS = ['@safrangroup.com', '@safran.fr']

    # Question secrète : liste prédéfinie
    SECURITY_QUESTIONS = [
        "Quel est le nom de votre premier animal de compagnie ?",
        "Dans quelle ville êtes-vous né(e) ?",
        "Quel est le nom de jeune fille de votre mère ?",
        "Quel était le modèle de votre première voiture ?",
        "Quel est le nom de votre école primaire ?"
    ]