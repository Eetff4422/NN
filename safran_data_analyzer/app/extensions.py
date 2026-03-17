from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialisation vide, on les reliera à l'application plus tard
db = SQLAlchemy()
login_manager = LoginManager()