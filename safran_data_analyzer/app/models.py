"""Définition des modèles de données (User, Report, LoginAttempt)."""
from app.extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    """
    Modèle représentant un utilisateur de l'application.
    """
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    secret_question = db.Column(db.String(255), nullable=False)
    secret_answer_hash = db.Column(db.String(128), nullable=False)
    password_hash = db.Column(db.String(128))

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


class Report(db.Model):
    """
    Modèle représentant un rapport d'analyse d'historique.
    Stocke : id, user_id, original_filename, stored_filename, uploaded_at, status, row_count, column_snapshot (JSON), graphs_json (JSON).
    """
    __tablename__ = 'report'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), nullable=False, default="success")
    row_count = db.Column(db.Integer, nullable=True)
    column_snapshot = db.Column(db.Text, nullable=True) # Stocké sous forme de string JSON
    graphs_json = db.Column(db.Text, nullable=True)     # Stocké sous forme de string JSON


class LoginAttempt(db.Model):
    """
    Modèle de suivi des tentatives de connexion pour bloquer le bruteforce (5 max/10min).
    """
    __tablename__ = 'login_attempt'
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)
    email_attempted = db.Column(db.String(120), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    success = db.Column(db.Boolean, default=False)


@login_manager.user_loader
def load_user(user_id):
    """Recharge l'utilisateur depuis la base de données."""
    return User.query.get(int(user_id))