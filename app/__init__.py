from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from app.config import Config

# Initialisation des extensions
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialisation des extensions avec l'application
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    
    # Configuration du login_manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'info'
    
    # Enregistrement des blueprints
    from app.routes.auth import auth
    from app.routes.profile import profile
    from app.routes.jobs import jobs
    from app.routes.history import history
    
    app.register_blueprint(auth)
    app.register_blueprint(profile)
    app.register_blueprint(jobs)
    app.register_blueprint(history)
    
    # Création des tables dans la base de données
    with app.app_context():
        db.create_all()
    
    return app
