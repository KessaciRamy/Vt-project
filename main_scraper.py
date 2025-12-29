"""
Script principal de collecte pour toutes les bases de données.

Ce script collecte les données depuis GitHub, RSS et NVD pour toutes
les bases de données configurées et sauvegarde les résultats en JSON.

Usage:
    python main_scraper.py                    # Toutes les BDD
    python main_scraper.py --db redis neo4j   # BDD spécifiques
    python main_scraper.py --output data.json # Fichier de sortie personnalisé
"""

import sys
import os
import json
import argparse
from datetime import datetime

# Fix PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from scrapers.universal_collector import UniversalCollector
from config.sources import get_all_databases, validate_database


def collect_all_databases(databases=None, releases_limit=10, posts_limit=10, cves_limit=20):
    """
    Collecter les données pour toutes les bases de données.
    
    Args:
        databases (list, optional): Liste des BDD à collecter. Si None, toutes les BDD.
        releases_limit (int): Nombre max de releases par BDD
        posts_limit (int): Nombre max d'articles par BDD
        cves_limit (int): Nombre max de CVE par BDD
    
    Returns:
        tuple: (all_data, stats)
    """
    # Si aucune BDD spécifiée, prendre toutes les BDD configurées
    if databases is None:
        databases = get_all_databases()
    
    # Valider les BDD
    invalid_dbs = [db for db in databases if not validate_database(db)]
    if invalid_dbs:
        print(f"⚠️  Bases de données non configurées: {', '.join(invalid_dbs)}")
        databases = [db for db in databases if validate_database(db)]
    
    if not databases:
        print("❌ Aucune base de données valide à collecter!")
        return [], {}
    
    print("\n" + "="*70)
    print(f"🚀 COLLECTE POUR {len(databases)} BASE(S) DE DONNÉES")
    print("="*70)
    print(f"Bases de données: {', '.join(databases)}")
    print(f"Limits: {releases_limit} releases, {posts_limit} articles, {cves_limit} CVE")
    print("="*70 + "\n")
    
    all_data = []
    global_stats = {
        'total_databases': len(databases),
        'successful_databases': 0,
        'failed_databases': 0,
        'total_items': 0,
        'total_releases': 0,
        'total_blog_posts': 0,
        'total_vulnerabilities': 0,
        'total_critical_cves': 0,
        'databases_stats': {},
        'errors': []
    }
    
    # Collecter pour chaque BDD
    for i, db in enumerate(databases, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(databases)}] Collecte de {db.upper()}")
        print(f"{'='*70}\n")
        
        try:
            # Créer le collector
            collector = UniversalCollector(db)
            
            # Collecter les données
            db_data = collector.collect_all(
                releases_limit=releases_limit,
                posts_limit=posts_limit,
                cves_limit=cves_limit
            )
            
            # Ajouter aux données globales
            all_data.extend(db_data)
            
            # Récupérer les stats
            db_stats = collector.get_statistics()
            global_stats['databases_stats'][db] = db_stats
            
            # Mettre à jour les stats globales
            global_stats['total_releases'] += db_stats['releases']
            global_stats['total_blog_posts'] += db_stats['blog_posts']
            global_stats['total_vulnerabilities'] += db_stats['vulnerabilities']
            global_stats['total_critical_cves'] += db_stats['critical_cves']
            global_stats['total_items'] += db_stats['total']
            
            if db_stats['total'] > 0:
                global_stats['successful_databases'] += 1
            
            # Ajouter les erreurs
            if db_stats['errors']:
                global_stats['errors'].extend([f"{db}: {err}" for err in db_stats['errors']])
        
        except Exception as e:
            error_msg = f"Erreur lors de la collecte de {db}: {str(e)}"
            print(f"\n❌ {error_msg}\n")
            global_stats['failed_databases'] += 1
            global_stats['errors'].append(error_msg)
    
    return all_data, global_stats


def save_to_json(data, filename='collected_data.json'):
    """
    Sauvegarder les données en JSON.
    
    Args:
        data (list): Données à sauvegarder
        filename (str): Nom du fichier
    
    Returns:
        bool: True si succès, False sinon
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Calculer la taille du fichier
        file_size = os.path.getsize(filename)
        size_mb = file_size / (1024 * 1024)
        
        print(f"\n💾 Données sauvegardées dans: {filename}")
        print(f"   Taille: {size_mb:.2f} MB ({file_size:,} bytes)")
        
        return True
    
    except Exception as e:
        print(f"\n❌ Erreur de sauvegarde: {e}")
        return False


def print_final_summary(stats):
    """
    Afficher le résumé final de la collecte.
    
    Args:
        stats (dict): Statistiques globales
    """
    print("\n" + "="*70)
    print("📊 RÉSUMÉ FINAL DE LA COLLECTE")
    print("="*70)
    
    print(f"\n🎯 Bases de données:")
    print(f"   Total traitées    : {stats['total_databases']}")
    print(f"   Succès            : {stats['successful_databases']} ✅")
    if stats['failed_databases'] > 0:
        print(f"   Échecs            : {stats['failed_databases']} ❌")
    
    print(f"\n📦 Données collectées:")
    print(f"   Releases (GitHub) : {stats['total_releases']}")
    print(f"   Articles (RSS)    : {stats['total_blog_posts']}")
    print(f"   CVE (NVD)         : {stats['total_vulnerabilities']}")
    if stats['total_critical_cves'] > 0:
        print(f"   CVE Critiques     : {stats['total_critical_cves']} ⚠️")
    print(f"   {'─'*68}")
    print(f"   TOTAL             : {stats['total_items']} éléments")
    
    # Détails par BDD
    if stats['databases_stats']:
        print(f"\n📈 Détails par base de données:")
        for db, db_stats in stats['databases_stats'].items():
            status = "✅" if db_stats['total'] > 0 else "⚠️"
            print(f"   {status} {db:15s} : {db_stats['total']:3d} éléments "
                  f"({db_stats['releases']}R + {db_stats['blog_posts']}A + {db_stats['vulnerabilities']}C)")
    
    # Erreurs
    if stats['errors']:
        print(f"\n⚠️  Erreurs ({len(stats['errors'])}):")
        for error in stats['errors'][:5]:  # Max 5 erreurs affichées
            print(f"   - {error}")
        if len(stats['errors']) > 5:
            print(f"   ... et {len(stats['errors']) - 5} autres erreurs")
    
    print("\n" + "="*70 + "\n")


def main():
    """Fonction principale."""
    # Parser les arguments
    parser = argparse.ArgumentParser(
        description='Collecter les données pour les bases de données NoSQL/NewSQL'
    )
    parser.add_argument(
        '--db',
        nargs='+',
        help='Bases de données à collecter (ex: redis neo4j). Si omis, toutes les BDD.'
    )
    parser.add_argument(
        '--output',
        default='collected_data.json',
        help='Fichier de sortie JSON (défaut: collected_data.json)'
    )
    parser.add_argument(
        '--releases',
        type=int,
        default=10,
        help='Nombre max de releases par BDD (défaut: 10)'
    )
    parser.add_argument(
        '--posts',
        type=int,
        default=10,
        help='Nombre max d\'articles par BDD (défaut: 10)'
    )
    parser.add_argument(
        '--cves',
        type=int,
        default=20,
        help='Nombre max de CVE par BDD (défaut: 20)'
    )
    
    args = parser.parse_args()
    
    # Afficher l'en-tête
    print("\n" + "="*70)
    print("🔍 MODULE DE SCRAPING - VEILLE TECHNOLOGIQUE NoSQL/NewSQL")
    print("="*70)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💾 Fichier de sortie: {args.output}")
    print("="*70)
    
    # Collecter les données
    try:
        all_data, stats = collect_all_databases(
            databases=args.db,
            releases_limit=args.releases,
            posts_limit=args.posts,
            cves_limit=args.cves
        )
        
        # Afficher le résumé
        print_final_summary(stats)
        
        # Sauvegarder
        if all_data:
            success = save_to_json(all_data, args.output)
            
            if success:
                print("✅ Collecte terminée avec succès!")
                print(f"\n💡 Les données sont prêtes pour l'intégration PostgreSQL.")
                print(f"   Fichier: {args.output}")
                return 0
            else:
                print("❌ Erreur lors de la sauvegarde")
                return 1
        else:
            print("⚠️  Aucune donnée collectée")
            return 1
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Collecte interrompue par l'utilisateur")
        return 1
    
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)