from app.extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    """
    Modèle représentant un utilisateur de l'application.

    Attributes:
        id (int): Identifiant unique de l'utilisateur.
        username (str): Nom d'utilisateur (trigramme).
        email (str): Adresse e-mail professionnelle.
        secret_question (str): Question de sécurité pour la récupération du mot de passe.
        secret_answer_hash (str): Hash de la réponse à la question de sécurité.
        password_hash (str): Hash du mot de passe de l'utilisateur.
        reports (list[Report]): Liste des rapports associés à l'utilisateur.
    """
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    secret_question = db.Column(db.String(255), nullable=False)
    secret_answer_hash = db.Column(db.String(128), nullable=False)
    password_hash = db.Column(db.String(128))

    # NOUVEAU : La relation avec l'historique. 
    # Si on supprime un utilisateur, on supprime aussi son historique (cascade)
    reports = db.relationship('Report', backref='author', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        """Définit le mot de passe de l'utilisateur après l'avoir haché."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Vérifie si le mot de passe fourni correspond au hash enregistré."""
        return check_password_hash(self.password_hash, password)

    def set_secret_answer(self, answer):
        """Définit la réponse à la question de sécurité après l'avoir hachée."""
        self.secret_answer_hash = generate_password_hash(answer.strip().lower())

    def check_secret_answer(self, answer):
        """Vérifie si la réponse à la question de sécurité correspond au hash enregistré."""
        return check_password_hash(self.secret_answer_hash, answer.strip().lower())

# NOUVEAU : La table qui mémorise les anciens fichiers
class Report(db.Model):
    """
    Modèle représentant un rapport d'analyse généré.

    Attributes:
        id (int): Identifiant unique du rapport.
        filename (str): Nom du fichier uploadé.
        filepath (str): Chemin d'accès au fichier sur le serveur.
        upload_date (datetime): Date et heure de l'upload.
        user_id (int): Identifiant de l'utilisateur ayant généré le rapport.
    """
    __tablename__ = 'report'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(512), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow) # Heure automatique
    
    # La clé étrangère qui lie ce rapport à un utilisateur précis
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    """
    Recharge l'utilisateur depuis la base de données à partir de son ID pour Flask-Login.
    """
    return User.query.get(int(user_id))