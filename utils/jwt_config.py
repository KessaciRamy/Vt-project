from flask_jwt_extended import JWTManager

def init_jwt(app):
    app.config["JWT_SECRET_KEY"] = "veille_secure_jwt_key"
    JWTManager(app)