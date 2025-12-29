"""
Universal Collector - Collecte depuis toutes les sources pour une BDD

Ce collector orchestre les 3 scrapers (GitHub, RSS, NVD) et collecte
toutes les données pour une base de données donnée.
"""

import sys
import os

# Fix PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import time
from scrapers.github_scraper import GitHubScraper
from scrapers.rss_scraper import RSSScraper
from scrapers.nvd_scraper import NVDScraper
from config.sources import get_database_config


class UniversalCollector:
    """
    Collector universel qui collecte depuis toutes les sources.
    
    Combine GitHub Scraper, RSS Scraper et NVD Scraper pour collecter
    toutes les informations disponibles sur une base de données.
    """
    
    def __init__(self, db_key):
        """
        Initialiser le Universal Collector.
        
        Args:
            db_key (str): Clé de la base de données (ex: "mongodb", "redis")
        
        Exemple:
            >>> collector = UniversalCollector('redis')
            >>> data = collector.collect_all()
        """
        self.db_key = db_key
        
        # Récupérer la config
        self.config = get_database_config(db_key)
        if not self.config:
            raise ValueError(f"Base de données '{db_key}' non configurée")
        
        self.name = self.config['name']
        
        # Initialiser les scrapers
        self.github_scraper = None
        self.rss_scraper = None
        self.nvd_scraper = None
        
        # Statistiques
        self.stats = {
            'releases': 0,
            'blog_posts': 0,
            'vulnerabilities': 0,
            'critical_cves': 0,
            'total': 0,
            'errors': []
        }
    
    
    def collect_all(self, releases_limit=5, posts_limit=5, cves_limit=10):
        """
        Collecter depuis toutes les sources disponibles.
        
        Args:
            releases_limit (int): Nombre max de releases GitHub
            posts_limit (int): Nombre max d'articles de blog
            cves_limit (int): Nombre max de CVE
        
        Returns:
            list: Liste de toutes les données collectées
        
        Exemple:
            >>> collector = UniversalCollector('redis')
            >>> all_data = collector.collect_all()
            >>> print(f"Collecté {len(all_data)} éléments")
        """
        print(f"\n{'='*70}")
        print(f"🔍 COLLECTE POUR {self.name}")
        print(f"{'='*70}\n")
        
        all_data = []
        
        # 1. Collecter les releases GitHub
        print("1️⃣ Collecte des releases GitHub...")
        releases = self._collect_github_releases(releases_limit)
        all_data.extend(releases)
        self.stats['releases'] = len(releases)
        time.sleep(1)  # Petite pause
        
        # 2. Collecter les articles de blog (RSS)
        print("\n2️⃣ Collecte des articles de blog (RSS)...")
        posts = self._collect_blog_posts(posts_limit)
        all_data.extend(posts)
        self.stats['blog_posts'] = len(posts)
        time.sleep(1)  # Petite pause
        
        # 3. Collecter les vulnérabilités (CVE)
        print("\n3️⃣ Collecte des vulnérabilités (CVE)...")
        cves = self._collect_vulnerabilities(cves_limit)
        all_data.extend(cves)
        self.stats['vulnerabilities'] = len(cves)
        
        # Compter les CVE critiques
        self.stats['critical_cves'] = sum(
            1 for item in cves if item.get('is_critical', False)
        )
        
        # Total
        self.stats['total'] = len(all_data)
        
        # Afficher le résumé
        self._print_summary()
        
        return all_data
    
    
    def _collect_github_releases(self, limit):
        """Collecter les releases GitHub"""
        try:
            self.github_scraper = GitHubScraper(self.db_key)
            releases = self.github_scraper.get_releases(limit=limit)
            
            if releases:
                print(f"   ✅ {len(releases)} releases collectées")
            else:
                print(f"   ⚠️  Aucune release trouvée")
            
            return releases
        
        except Exception as e:
            error_msg = f"GitHub: {str(e)}"
            print(f"   ❌ Erreur: {error_msg}")
            self.stats['errors'].append(error_msg)
            return []
    
    
    def _collect_blog_posts(self, limit):
        """Collecter les articles de blog via RSS"""
        try:
            self.rss_scraper = RSSScraper(self.db_key)
            posts = self.rss_scraper.get_blog_posts(limit=limit)
            
            if posts:
                print(f"   ✅ {len(posts)} articles collectés")
            else:
                print(f"   ⚠️  Aucun article trouvé")
            
            return posts
        
        except Exception as e:
            error_msg = f"RSS: {str(e)}"
            print(f"   ❌ Erreur: {error_msg}")
            self.stats['errors'].append(error_msg)
            return []
    
    
    def _collect_vulnerabilities(self, limit):
        """Collecter les vulnérabilités depuis NVD"""
        try:
            self.nvd_scraper = NVDScraper(self.db_key)
            cves = self.nvd_scraper.get_vulnerabilities(limit=limit)
            
            if cves:
                print(f"   ✅ {len(cves)} CVE collectés")
                
                # Compter les critiques
                critical_count = sum(1 for cve in cves if cve.get('is_critical', False))
                if critical_count > 0:
                    print(f"   ⚠️  {critical_count} CVE critiques/élevés!")
            else:
                print(f"   ⚠️  Aucun CVE trouvé")
            
            return cves
        
        except Exception as e:
            error_msg = f"NVD: {str(e)}"
            print(f"   ❌ Erreur: {error_msg}")
            self.stats['errors'].append(error_msg)
            return []
    
    
    def _print_summary(self):
        """Afficher le résumé de la collecte"""
        print(f"\n{'='*70}")
        print(f"📊 RÉSUMÉ - {self.name}")
        print(f"{'='*70}")
        print(f"   Releases (GitHub)  : {self.stats['releases']}")
        print(f"   Articles (RSS)     : {self.stats['blog_posts']}")
        print(f"   CVE (NVD)          : {self.stats['vulnerabilities']}")
        if self.stats['critical_cves'] > 0:
            print(f"   CVE Critiques      : {self.stats['critical_cves']} ⚠️")
        print(f"   {'─'*68}")
        print(f"   TOTAL              : {self.stats['total']} éléments")
        
        if self.stats['errors']:
            print(f"\n   ⚠️  Erreurs ({len(self.stats['errors'])}):")
            for error in self.stats['errors']:
                print(f"      - {error}")
        
        print(f"{'='*70}\n")
    
    
    def get_statistics(self):
        """
        Récupérer les statistiques de la collecte.
        
        Returns:
            dict: Statistiques détaillées
        """
        return self.stats.copy()


# ============================================
# TESTS
# ============================================

if __name__ == "__main__":
    """
    Tests du Universal Collector.
    Lance avec: python -m scrapers.universal_collector
    """
    
    print("\n" + "="*70)
    print("🧪 TEST DU UNIVERSAL COLLECTOR")
    print("="*70 + "\n")
    
    # Test avec Redis (a beaucoup de données)
    print("Test avec Redis:")
    print("-" * 70)
    
    try:
        collector = UniversalCollector('redis')
        
        # Collecter toutes les données
        all_data = collector.collect_all(
            releases_limit=3,
            posts_limit=3,
            cves_limit=5
        )
        
        # Afficher quelques exemples
        if all_data:
            print("📝 Exemples de données collectées:\n")
            
            # Grouper par type
            by_type = {}
            for item in all_data:
                item_type = item['type']
                if item_type not in by_type:
                    by_type[item_type] = []
                by_type[item_type].append(item)
            
            # Afficher des exemples de chaque type
            for data_type, items in by_type.items():
                print(f"   {data_type.upper()} ({len(items)}):")
                for item in items[:2]:  # Juste 2 exemples
                    print(f"      - {item['title'][:50]}...")
                print()
        
        # Statistiques
        stats = collector.get_statistics()
        print("✅ Test réussi!")
        print(f"   Total collecté: {stats['total']} éléments")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("✅ TEST TERMINÉ")
    print("="*70 + "\n")