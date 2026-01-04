from flask import Blueprint, jsonify, request
from traitement.data_processor import run_data_processing_api
from db_insertion import DatabaseIngestor
from models.db_config import DB_CONFIG
import os

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
        process_result = run_data_processing_api(
            input_file=input_file,
            output_file=output_file
        )

        if process_result["items_cleaned"] == 0:
            return jsonify({
            "error": "Aucune donnee valide apres traitement",
            "processing_stats": process_result
            }), 400

        ingestor = DatabaseIngestor(DB_CONFIG)
        insert_stats = ingestor.ingest(output_file)
        ingestor.close()
        return jsonify({
            "message": "Traitement et insertion terminés avec succès",
            "processing": process_result,
            "insertion": insert_stats
        }), 200
    
    except Exception as e:
        return jsonify({
            "error": "Erreur lors du traitement des données->insertion",
            "details": str(e)
        }), 500