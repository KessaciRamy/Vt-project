from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from models.db_connection import get_connection

notif_bp = Blueprint("notifications", __name__)

# notifications est l'URL
@notif_bp.route("/notifications", methods=["GET"]) 
@jwt_required()
def get_notifications():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT cve_id, title, severity, cvss_score, published_date
        FROM vulnerabilities
        WHERE is_critical = true
        ORDER BY published_date DESC
        LIMIT 20
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    notifs = []
    for r in rows:
        notifs.append({
            "cve_id": r[0],
            "title": r[1],
            "severity": r[2],
            "cvss_score": float(r[3]),
            "published_date": r[4]
        })

    return jsonify(notifs)
