from flask import Flask
from routes.veilleur import veilleur_bp
from routes.analyst import analyste_bp
from routes.auth import auth_bp
from routes.data_api import data_bp
from routes.notif import notif_bp
from routes.create_user import create_user_bp

from models.init_db import create_tables
from utils.jwt_config import init_jwt

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    #creation de bdd et ces tables 
    create_tables()
    
    init_jwt(app)

    app.register_blueprint(veilleur_bp, url_prefix="/veilleur")
    app.register_blueprint(analyste_bp, url_prefix="/analyste")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(create_user_bp, url_prefix="/users")
    app.register_blueprint(data_bp, url_prefix="/data_api")
    app.register_blueprint(notif_bp, url_prefix="/notifications")
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)