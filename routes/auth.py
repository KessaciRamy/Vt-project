from flask import Blueprint, request, jsonify
import psycopg2
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token
from models.db_connection import get_connection

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    compte = data.get("compte")
    password = data.get("password")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT password, user_type FROM users WHERE compte=%s",
        (compte,)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        return jsonify({"error": "Utilisateur introuvable"}), 401

    hashed_password, user_type = user

    if not check_password_hash(hashed_password, password):
        return jsonify({"error": "Mot de passe incorrect"}), 401

    # JWT enrichi avec le type
    token = create_access_token(
        identity= compte,
        additional_claims={"user_type": user_type}
    )

    return jsonify({
        "access_token": token,
        "user_type": user_type
    })
