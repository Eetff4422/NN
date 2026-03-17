from app.extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
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
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_secret_answer(self, answer):
        self.secret_answer_hash = generate_password_hash(answer.strip().lower())

    def check_secret_answer(self, answer):
        return check_password_hash(self.secret_answer_hash, answer.strip().lower())

# NOUVEAU : La table qui mémorise les anciens fichiers
class Report(db.Model):
    __tablename__ = 'report'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(512), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow) # Heure automatique
    
    # La clé étrangère qui lie ce rapport à un utilisateur précis
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))