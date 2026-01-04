from flask import Blueprint, jsonify, request
from main_scraper import run_scraper_api

veilleur_bp = Blueprint("veilleur", __name__)

@veilleur_bp.route("/scrap", methods=["POST"])
def launch_scraping():
    body = request.get_json(silent=True) or {}

    databases = body.get("databases")
    releases = body.get("releases", 10)
    posts = body.get("posts", 10)
    cves = body.get("cves", 20)

    try:
        result = run_scraper_api(
            databases=databases,
            releases_limit=releases,
            posts_limit=posts,
            cves_limit=cves,
            output_file="collected_data.json"
        )

        return jsonify({
            "message": "Scraping reussi !",
            "result": result
        }), 200
    
    except Exception as e:
        return jsonify({
            "error": "Erreur lors du scraping",
            "details": str(e)
        }), 500