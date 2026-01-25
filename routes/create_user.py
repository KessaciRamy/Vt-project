from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from models.db_connection import get_connection

create_user_bp = Blueprint("create_user", __name__)

@create_user_bp.route("/create", methods=["POST"])
def create_user():
    data = request.get_json()

    compte = data.get("compte")
    password = data.get("password")
    user_type = data.get("user_type")

    if not compte or not password or not user_type:
        return jsonify({
            "error": "compte, password et user_type sont requis"
        }), 400

    if user_type not in ("veilleur", "analyste", "decideur"):
        return jsonify({
            "error": "user_type invalide"
        }), 400

    hashed_password = generate_password_hash(password)

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO users (compte, password, user_type)
            VALUES (%s, %s, %s)
        """, (compte, hashed_password, user_type))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "message": "Utilisateur créé avec succès",
            "compte": compte,
            "user_type": user_type
        }), 201

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Erreur lors de la création de l'utilisateur",
            "details": str(e)
        }), 500