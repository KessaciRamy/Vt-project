"""
GitHub Scraper - Collecte les releases depuis l'API GitHub

Ce scraper récupère les informations sur les nouvelles versions
(releases) des bases de données depuis leurs repositories GitHub.
"""

import sys
import os

# Fix PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import time
from datetime import datetime
from dotenv import load_dotenv
from scrapers.base_scraper import BaseScraper
from config.sources import get_github_info

# Charger les variables d'environnement depuis .env
load_dotenv()


class GitHubScraper(BaseScraper):
    """
    Scraper pour collecter les releases depuis GitHub.
    
    Utilise l'API GitHub pour récupérer les informations sur les versions
    publiées d'une base de données.
    """
    
    def __init__(self, db_key, token=None):
        """
        Initialiser le GitHub Scraper.
        
        Args:
            db_key (str): Clé de la base de données (ex: "mongodb")
            token (str, optional): Token GitHub pour augmenter le rate limit
        
        Exemple:
            >>> scraper = GitHubScraper('mongodb')
            >>> scraper = GitHubScraper('mongodb', token='ghp_xxxxx')
        """
        # Appeler le constructeur parent
        super().__init__(db_key)
        
        # Récupérer les infos GitHub depuis la config
        self.github_info = get_github_info(db_key)
        
        if not self.github_info:
            raise ValueError(f"Pas d'informations GitHub pour '{db_key}' dans la config")
        
        # Extraire owner et repo
        self.owner = self.github_info['owner']
        self.repo = self.github_info['repo']
        
        # Token GitHub (optionnel)
        self.token = token
        if not self.token:
            # Essayer de récupérer depuis variable d'environnement
            self.token = os.getenv('GITHUB_TOKEN')
        
        # Ajouter le token aux headers si présent
        if self.token:
            self.headers['Authorization'] = f'Bearer {self.token}'
            print(f"✅ [{self.name}] Token GitHub configuré")
        else:
            print(f"⚠️  [{self.name}] Pas de token GitHub (limite: 60 req/h)")
        
        # URL de base de l'API
        self.api_base = "https://api.github.com"
    
    
    def get_releases(self, limit=10):
        """
        Récupérer les releases depuis GitHub.
        
        Args:
            limit (int): Nombre maximum de releases à récupérer
        
        Returns:
            list: Liste de dictionnaires contenant les releases
        
        Exemple:
            >>> scraper = GitHubScraper('mongodb')
            >>> releases = scraper.get_releases(limit=5)
            >>> print(f"Trouvé {len(releases)} releases")
        """
        # Construire l'URL
        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/releases"
        
        # Log
        print(f"🔍 [{self.name}] Collecte des releases depuis GitHub...")
        print(f"   Repository: {self.owner}/{self.repo}")
        
        # Faire la requête
        response = self.make_request(url)
        
        if not response or response.status_code != 200:
            print(f"❌ [{self.name}] Échec de la collecte des releases")
            return []
        
        # Parser la réponse JSON
        try:
            releases_data = response.json()
        except Exception as e:
            print(f"❌ [{self.name}] Erreur de parsing JSON: {e}")
            return []
        
        # Traiter les releases
        releases = []
        for release in releases_data[:limit]:
            try:
                # Extraire les informations
                processed_release = self._process_release(release)
                if processed_release:
                    releases.append(processed_release)
            except Exception as e:
                print(f"⚠️  [{self.name}] Erreur sur une release: {e}")
                continue
        
        print(f"✅ [{self.name}] {len(releases)} releases collectées")
        
        return releases
    
    
    def _process_release(self, release):
        """
        Traiter une release GitHub et extraire les infos importantes.
        
        Args:
            release (dict): Données brutes d'une release depuis l'API GitHub
        
        Returns:
            dict: Données structurées de la release
        """
        # Extraire les champs de base
        tag_name = release.get('tag_name', '')
        name = release.get('name', tag_name)
        body = release.get('body', '')
        published_at = release.get('published_at', '')
        html_url = release.get('html_url', '')
        prerelease = release.get('prerelease', False)
        draft = release.get('draft', False)
        
        # Nettoyer la version (enlever 'v', 'r', etc.)
        version = self._clean_version(tag_name)
        
        # Nettoyer et tronquer la description
        description = self._clean_description(body)
        
        # Normaliser la date
        date = self._normalize_date(published_at)
        
        # Créer l'entrée avec le format uniforme
        entry = self.create_data_entry(
            source='github',
            data_type='release',
            title=name or f"Release {version}",
            date=date,
            description=description,
            url=html_url,
            # Champs spécifiques aux releases
            version=version,
            tag_name=tag_name,
            is_prerelease=prerelease,
            is_draft=draft
        )
        
        return entry
    
    
    def _clean_version(self, tag_name):
        """
        Nettoyer le numéro de version.
        
        Args:
            tag_name (str): Tag GitHub (ex: "v7.0.0", "r6.2.1")
        
        Returns:
            str: Version nettoyée (ex: "7.0.0")
        """
        # Enlever les préfixes communs
        version = tag_name.lower()
        for prefix in ['v', 'r', 'release-', 'version-']:
            if version.startswith(prefix):
                version = version[len(prefix):]
                break
        
        return version or tag_name
    
    
    def _clean_description(self, body):
        """
        Nettoyer et tronquer la description.
        
        Args:
            body (str): Description complète de la release
        
        Returns:
            str: Description nettoyée et tronquée
        """
        if not body:
            return "Pas de description disponible"
        
        # Enlever les caractères de contrôle
        description = body.strip()
        
        # Tronquer si trop long (garder 1000 caractères)
        if len(description) > 1000:
            description = description[:997] + "..."
        
        return description
    
    
    def _normalize_date(self, date_string):
        """
        Normaliser une date au format YYYY-MM-DD.
        
        Args:
            date_string (str): Date au format ISO (ex: "2023-08-28T14:30:00Z")
        
        Returns:
            str: Date normalisée (ex: "2023-08-28")
        """
        if not date_string:
            return datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Parser la date ISO
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
        except Exception:
            # Si échec, retourner la date actuelle
            return datetime.now().strftime('%Y-%m-%d')
    
    
    def check_rate_limit(self):
        """
        Vérifier le rate limit restant de l'API GitHub.
        
        Returns:
            dict: Informations sur le rate limit
        
        Exemple:
            >>> scraper = GitHubScraper('mongodb')
            >>> info = scraper.check_rate_limit()
            >>> print(f"Restant: {info['remaining']}/{info['limit']}")
        """
        url = f"{self.api_base}/rate_limit"
        
        response = self.make_request(url)
        
        if not response or response.status_code != 200:
            return None
        
        try:
            data = response.json()
            core = data['resources']['core']
            
            return {
                'limit': core['limit'],
                'remaining': core['remaining'],
                'reset_at': datetime.fromtimestamp(core['reset']).strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            print(f"❌ Erreur de parsing rate limit: {e}")
            return None
    
    
    def get_latest_release(self):
        """
        Récupérer uniquement la dernière release.
        
        Returns:
            dict: Dernière release ou None
        
        Exemple:
            >>> scraper = GitHubScraper('mongodb')
            >>> latest = scraper.get_latest_release()
            >>> print(f"Dernière version: {latest['version']}")
        """
        releases = self.get_releases(limit=1)
        return releases[0] if releases else None


# ============================================
# TESTS
# ============================================

if __name__ == "__main__":
    """
    Tests du GitHub Scraper.
    Lance avec: python -m scrapers.github_scraper
    """
    
    print("\n" + "="*60)
    print("🧪 TEST DU GITHUB SCRAPER")
    print("="*60 + "\n")
    
    # Test 1: Initialisation
    print("1️⃣ Test d'initialisation")
    print("-" * 60)
    try:
        scraper = GitHubScraper('mongodb')
        print(f"✅ GitHub Scraper créé pour {scraper.name}")
        print(f"   Repository: {scraper.owner}/{scraper.repo}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        exit(1)
    print()
    
    # Test 2: Récupération des releases
    print("2️⃣ Test de récupération des releases")
    print("-" * 60)
    try:
        releases = scraper.get_releases(limit=3)
        
        if releases:
            print(f"✅ {len(releases)} releases récupérées\n")
            
            # Afficher les détails de la première release
            latest = releases[0]
            print("   Dernière release:")
            print(f"   📦 Version: {latest['version']}")
            print(f"   📅 Date: {latest['date']}")
            print(f"   📝 Titre: {latest['title']}")
            print(f"   🔗 URL: {latest['url']}")
            print(f"   📄 Description: {latest['description'][:100]}...")
        else:
            print("⚠️  Aucune release trouvée")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    print()
    
    # Test 3: Vérification du rate limit
    print("3️⃣ Test du rate limit GitHub")
    print("-" * 60)
    try:
        rate_info = scraper.check_rate_limit()
        
        if rate_info:
            print(f"✅ Rate limit:")
            print(f"   Limite: {rate_info['limit']} requêtes/heure")
            print(f"   Restant: {rate_info['remaining']}")
            print(f"   Reset à: {rate_info['reset_at']}")
            
            # Avertissement si proche de la limite
            if rate_info['remaining'] < 10:
                print(f"\n   ⚠️  Attention: Seulement {rate_info['remaining']} requêtes restantes!")
        else:
            print("⚠️  Impossible de vérifier le rate limit")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    print()
    
    # Test 4: Dernière release uniquement
    print("4️⃣ Test de récupération de la dernière release")
    print("-" * 60)
    try:
        latest = scraper.get_latest_release()
        
        if latest:
            print(f"✅ Dernière version: {latest['version']}")
            print(f"   Publiée le: {latest['date']}")
        else:
            print("⚠️  Aucune release trouvée")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    print()
    
    # Test 5: Statistiques
    print("5️⃣ Statistiques")
    print("-" * 60)
    stats = scraper.get_statistics()
    print(f"   Total requêtes: {stats['total_requests']}")
    print(f"   Succès: {stats['successful']}")
    print(f"   Erreurs: {stats['errors']}")
    print(f"   Taux de succès: {stats['success_rate']}%")
    print()
    
    print("="*60)
    print("✅ TESTS GITHUB SCRAPER TERMINÉS")
    print("="*60 + "\n")