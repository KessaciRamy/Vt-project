from flask import Blueprint, jsonify, request
from traitement.data_processor import run_data_processing_api
from db_insertion import DatabaseIngestor
from models.db_config import DB_CONFIG
import os
from flask import Blueprint, jsonify, request, render_template
from text_summarizer import summarize_blog_posts 

# Importer le nouveau module
from text_summarizer import summarize_blog_posts  # Ajoutez cette ligne

analyste_bp = Blueprint("analyste", __name__)

@analyste_bp.route("/process", methods=["POST"])
def process_data():
    body = request.get_json(silent=True) or {}

    input_file = body.get("input_file", "collected_data.json")
    output_file = body.get("output_file", "cleaned_data.json")

    if not os.path.exists(input_file):
        return jsonify({
            "error": "Fichier collected_data.json introuvable",
            "path": input_file
        }), 404
    
    try:
        # 1. Traitement des données
        process_result = run_data_processing_api(
            input_file=input_file,
            output_file=output_file
        )

        if process_result["items_cleaned"] == 0:
            return jsonify({
                "error": "Aucune donnee valide apres traitement",
                "processing_stats": process_result
            }), 400

        # 2. Insertion en base de données
        ingestor = DatabaseIngestor(DB_CONFIG)
        insert_stats = ingestor.ingest(output_file)
        ingestor.close()

        # 3. ANALYSE ET RÉSUMÉ DES ARTICLES (NOUVEAU)
        summary_result = summarize_blog_posts(output_file)
        
        return jsonify({
            "message": "Traitement, insertion et analyse terminés avec succès",
            "processing": process_result,
            "insertion": insert_stats,
            "summary_analysis": summary_result  # Ajouté
        }), 200
    
    except Exception as e:
        return jsonify({
            "error": "Erreur lors du traitement des données->insertion->analyse",
            "details": str(e)
        }), 500


@analyste_bp.route("/analyze", methods=["POST"])
def analyze_only():
    """
    Endpoint pour analyser les articles sans traitement complet.
    """
    body = request.get_json(silent=True) or {}
    
    input_file = body.get("input_file", "cleaned_data.json")
    
    if not os.path.exists(input_file):
        return jsonify({
            "error": f"Fichier {input_file} introuvable",
            "path": input_file
        }), 404
    
    try:
        summary_result = summarize_blog_posts(input_file)
        
        if 'error' in summary_result:
            return jsonify(summary_result), 400
        
        return jsonify({
            "message": "Analyse terminée avec succès",
            "analysis": summary_result
        }), 200
    
    except Exception as e:
        return jsonify({
            "error": f"Erreur lors de l'analyse: {str(e)}"
        }), 500


@analyste_bp.route("/check-file", methods=["GET"])
def check_file():
    """Vérifier si un fichier existe."""
    filename = request.args.get('file', '')
    
    if not filename:
        return jsonify({"error": "Nom de fichier requis"}), 400
    
    file_exists = os.path.exists(filename)
    
    return jsonify({
        "filename": filename,
        "exists": file_exists,
        "size": os.path.getsize(filename) if file_exists else 0
    }), 200

@analyste_bp.route("/analyze-blog", methods=["GET"])
def analyze_blog_page():
    """
    Page HTML pour afficher l'analyse des articles.
    """
    return render_template("analyze_blog.html")
