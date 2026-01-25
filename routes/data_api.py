from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models.db_connection import get_connection

data_bp = Blueprint("data_api", __name__)

# =========================
# DATABASES
# =========================
@data_bp.route("/databases", methods=["GET"])
@jwt_required()
def get_databases():
    compte = get_jwt_identity()
    claims = get_jwt()
    user_type = claims["user_type"]
    if user_type != 'decideur':
        return jsonify({"error": "Accès refusé"}), 403
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, category, official_site, github_url, last_scraped
        FROM databases
        WHERE is_active = true
    """)
    rows = cur.fetchall()

    cur.close()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "id": r[0],
            "name": r[1],
            "category": r[2],
            "official_site": r[3],
            "github_url": r[4],
            "last_scraped": r[5]
        })

    return jsonify(result)


# =========================
# RELEASES
# =========================
@data_bp.route("/databases/<int:db_id>/releases", methods=["GET"])
@jwt_required()
def get_releases(db_id):
    compte = get_jwt_identity()
    claims = get_jwt()
    user_type = claims["user_type"]
    if user_type != 'decideur':
        return jsonify({"error": "Accès refusé"}), 403
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT version, title, description, release_date, url,
               is_prerelease, has_breaking_changes
        FROM releases
        WHERE database_id = %s
        ORDER BY release_date DESC
    """, (db_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([
        {
            "version": r[0],
            "title": r[1],
            "description": r[2],
            "release_date": r[3],
            "url": r[4],
            "is_prerelease": r[5],
            "has_breaking_changes": r[6]
        } for r in rows
    ])


# =========================
# BLOG POSTS
# =========================
@data_bp.route("/databases/<int:db_id>/blogs", methods=["GET"])
@jwt_required()
def get_blog_posts(db_id):
    compte = get_jwt_identity()
    claims = get_jwt()
    user_type = claims["user_type"]
    if user_type != 'decideur':
        return jsonify({"error": "Accès refusé"}), 403
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT title, description, published_date, url, author, category
        FROM blog_posts
        WHERE database_id = %s
        ORDER BY published_date DESC
    """, (db_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([
        {
            "title": r[0],
            "description": r[1],
            "published_date": r[2],
            "url": r[3],
            "author": r[4],
            "category": r[5]
        } for r in rows
    ])


# =========================
# VULNERABILITIES
# =========================
@data_bp.route("/databases/<int:db_id>/vulnerabilities", methods=["GET"])
@jwt_required()
def get_vulnerabilities(db_id):
    compte = get_jwt_identity()
    claims = get_jwt()
    user_type = claims["user_type"]
    if user_type != 'decideur':
        return jsonify({"error": "Accès refusé"}), 403
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT cve_id, title, severity, cvss_score,
               published_date, url, is_critical
        FROM vulnerabilities
        WHERE database_id = %s
        ORDER BY cvss_score DESC
    """, (db_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([
        {
            "cve_id": r[0],
            "title": r[1],
            "severity": r[2],
            "cvss_score": float(r[3]) if r[3] else None,
            "published_date": r[4],
            "url": r[5],
            "is_critical": r[6]
        } for r in rows
    ])


# =========================
# KEYWORDS
# =========================
@data_bp.route("/databases/<int:db_id>/keywords", methods=["GET"])
@jwt_required()
def get_keywords(db_id):
    compte = get_jwt_identity()
    claims = get_jwt()
    user_type = claims["user_type"]
    if user_type != 'decideur':
        return jsonify({"error": "Accès refusé"}), 403
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT keyword, category, occurrences
        FROM keywords
        WHERE database_id = %s
        ORDER BY occurrences DESC
    """, (db_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([
        {
            "keyword": r[0],
            "category": r[1],
            "occurrences": r[2]
        } for r in rows
    ])