"""
Script principal d'intégration - Pipeline complet.

Ce script orchestre tout le processus:
1. Collecte (main_scraper.py - optionnel)
2. Traitement (data_processor.py)
3. Intégration PostgreSQL (db_integration.py)

Usage:
    python main_integration.py                    # Pipeline complet
    python main_integration.py --skip-scraping   # Sauter la collecte
    python main_integration.py --config db.ini   # Config custom
"""

import sys
import os
import argparse
import json
import configparser
from datetime import datetime
from data_processor import DataProcessor
from db_integration import DatabaseIntegrator


def load_db_config(config_file='database.ini'):
    """
    Charger la configuration PostgreSQL depuis un fichier INI.
    
    Args:
        config_file: Chemin vers le fichier de config
    
    Returns:
        Dict avec la configuration
    """
    if not os.path.exists(config_file):
        # Configuration par défaut
        print(f"⚠️  Fichier {config_file} non trouvé, utilisation config par défaut")
        return {
            'host': 'localhost',
            'port': 5432,
            'database': 'veille_nosql',
            'user': 'postgres',
            'password': 'password'
        }
    
    config = configparser.ConfigParser()
    config.read(config_file)
    
    db_config = {
        'host': config.get('postgresql', 'host', fallback='localhost'),
        'port': config.getint('postgresql', 'port', fallback=5432),
        'database': config.get('postgresql', 'database', fallback='veille_nosql'),
        'user': config.get('postgresql', 'user', fallback='postgres'),
        'password': config.get('postgresql', 'password', fallback='password')
    }
    
    print(f"✅ Configuration chargée depuis {config_file}")
    return db_config


def run_scraping():
    """Lancer le scraping"""
    print("\n" + "="*70)
    print("🕷️  ÉTAPE 1: COLLECTE DES DONNÉES (SCRAPING)")
    print("="*70 + "\n")
    
    try:
        # Importer et lancer le scraper
        import main_scraper
        
        # Lancer la collecte
        all_data, stats = main_scraper.collect_all_databases(
            databases=None,  # Toutes les BDD
            releases_limit=10,
            posts_limit=10,
            cves_limit=20
        )
        
        # Sauvegarder
        if all_data:
            success = main_scraper.save_to_json(all_data, 'collected_data.json')
            if success:
                print("✅ Collecte terminée avec succès!")
                return True
        
        print("⚠️  Aucune donnée collectée")
        return False
    
    except Exception as e:
        print(f"❌ Erreur lors du scraping: {e}")
        return False


def run_processing():
    """Lancer le traitement des données"""
    print("\n" + "="*70)
    print("🔧 ÉTAPE 2: TRAITEMENT DES DONNÉES")
    print("="*70 + "\n")
    
    # Vérifier que collected_data.json existe
    if not os.path.exists('collected_data.json'):
        print("❌ Fichier collected_data.json non trouvé!")
        print("   Lancez d'abord le scraping ou placez le fichier manuellement.")
        return False
    
    try:
        # Créer le processeur
        processor = DataProcessor('collected_data.json')
        
        # Traiter les données
        cleaned_data = processor.process_all()
        
        if cleaned_data:
            # Sauvegarder les données nettoyées
            processor.save_cleaned_data('cleaned_data.json')
            print("✅ Traitement terminé avec succès!")
            return True
        else:
            print("❌ Aucune donnée traitée")
            return False
    
    except Exception as e:
        print(f"❌ Erreur lors du traitement: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_integration(db_config):
    """Lancer l'intégration PostgreSQL"""
    print("\n" + "="*70)
    print("🗄️  ÉTAPE 3: INTÉGRATION POSTGRESQL")
    print("="*70 + "\n")
    
    # Vérifier que cleaned_data.json existe
    if not os.path.exists('cleaned_data.json'):
        print("❌ Fichier cleaned_data.json non trouvé!")
        print("   Lancez d'abord le traitement.")
        return False
    
    try:
        # Charger les données nettoyées
        print("📂 Chargement des données nettoyées...")
        with open('cleaned_data.json', 'r', encoding='utf-8') as f:
            cleaned_data = json.load(f)
        print(f"✅ {len(cleaned_data)} éléments chargés\n")
        
        # Créer l'intégrateur
        integrator = DatabaseIntegrator(db_config)
        
        # Se connecter
        if not integrator.connect():
            print("❌ Impossible de se connecter à PostgreSQL")
            print("   Vérifiez votre configuration dans database.ini")
            return False
        
        try:
            # Créer les tables
            integrator.create_tables()
            
            # Intégrer les données
            integrator.integrate_all(cleaned_data)
            
            print("✅ Intégration terminée avec succès!")
            return True
        
        finally:
            # Toujours fermer la connexion
            integrator.disconnect()
    
    except FileNotFoundError:
        print("❌ Fichier cleaned_data.json non trouvé!")
        return False
    
    except Exception as e:
        print(f"❌ Erreur lors de l'intégration: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_sample_config():
    """Créer un fichier de configuration exemple"""
    config_content = """[postgresql]
host = localhost
port = 5432
database = veille_nosql
user = postgres
password = your_password_here

# Instructions:
# 1. Modifiez les valeurs ci-dessus selon votre configuration PostgreSQL
# 2. Assurez-vous que la base de données existe:
#    CREATE DATABASE veille_nosql;
# 3. Sauvegardez ce fichier
"""
    
    try:
        with open('database.ini', 'w', encoding='utf-8') as f:
            f.write(config_content)
        print("✅ Fichier database.ini créé")
        print("   Modifiez-le avec vos paramètres PostgreSQL!")
        return True
    except Exception as e:
        print(f"❌ Erreur création database.ini: {e}")
        return False


def print_header():
    """Afficher l'en-tête du programme"""
    print("\n" + "="*70)
    print("🚀 PIPELINE D'INTÉGRATION - VEILLE NOSQL/NEWSQL")
    print("="*70)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")


def print_final_summary(results):
    """Afficher le résumé final"""
    print("\n" + "="*70)
    print("📊 RÉSUMÉ FINAL DU PIPELINE")
    print("="*70)
    
    for step, success in results.items():
        status = "✅" if success else "❌"
        print(f"   {status} {step}")
    
    all_success = all(results.values())
    
    if all_success:
        print("\n🎉 PIPELINE TERMINÉ AVEC SUCCÈS!")
        print("\n💡 Prochaines étapes:")
        print("   1. Vérifiez les données dans PostgreSQL")
        print("   2. Créez des vues et dashboards")
        print("   3. Configurez l'analyse automatique")
    else:
        print("\n⚠️  Le pipeline a rencontré des erreurs")
        print("   Consultez les logs ci-dessus pour plus de détails")
    
    print("="*70 + "\n")


def main():
    """Fonction principale"""
    
    # Parser les arguments
    parser = argparse.ArgumentParser(
        description='Pipeline complet d\'intégration des données de veille'
    )
    parser.add_argument(
        '--skip-scraping',
        action='store_true',
        help='Sauter l\'étape de scraping (utiliser collected_data.json existant)'
    )
    parser.add_argument(
        '--skip-processing',
        action='store_true',
        help='Sauter l\'étape de traitement (utiliser cleaned_data.json existant)'
    )
    parser.add_argument(
        '--config',
        default='database.ini',
        help='Fichier de configuration PostgreSQL (défaut: database.ini)'
    )
    parser.add_argument(
        '--create-config',
        action='store_true',
        help='Créer un fichier database.ini exemple'
    )
    
    args = parser.parse_args()
    
    # Créer config si demandé
    if args.create_config:
        create_sample_config()
        return 0
    
    # Afficher l'en-tête
    print_header()
    
    # Résultats de chaque étape
    results = {}
    
    # ÉTAPE 1: Scraping (optionnel)
    if not args.skip_scraping:
        results['Scraping'] = run_scraping()
        if not results['Scraping']:
            print("\n⚠️  Scraping échoué, vérifiez que collected_data.json existe")
            if not os.path.exists('collected_data.json'):
                print("❌ Impossible de continuer sans données")
                return 1
    else:
        print("\n⏭️  Étape de scraping ignorée (--skip-scraping)")
        if not os.path.exists('collected_data.json'):
            print("❌ Fichier collected_data.json non trouvé!")
            return 1
        results['Scraping'] = True
    
    # ÉTAPE 2: Traitement
    if not args.skip_processing:
        results['Traitement'] = run_processing()
        if not results['Traitement']:
            print("❌ Traitement échoué, impossible de continuer")
            print_final_summary(results)
            return 1
    else:
        print("\n⏭️  Étape de traitement ignorée (--skip-processing)")
        if not os.path.exists('cleaned_data.json'):
            print("❌ Fichier cleaned_data.json non trouvé!")
            return 1
        results['Traitement'] = True
    
    # ÉTAPE 3: Intégration PostgreSQL
    # Charger la configuration
    db_config = load_db_config(args.config)
    results['Intégration'] = run_integration(db_config)
    
    # Afficher le résumé final
    print_final_summary(results)
    
    # Code de sortie
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
