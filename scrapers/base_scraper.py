"""
Classe de base pour tous les scrapers.

Cette classe fournit des fonctionnalités communes à tous les scrapers :
- Gestion des requêtes HTTP avec retry
- Gestion des erreurs
- Rate limiting
- Logging
- Format de données uniforme
"""

import requests
import time
from datetime import datetime
from config.sources import get_database_config


class BaseScraper:
    """
    Classe de base pour tous les scrapers.
    
    Fournit des méthodes communes pour faire des requêtes HTTP,
    gérer les erreurs, respecter les rate limits, etc.
    """
    
    def __init__(self, db_key):
        """
        Initialiser le scraper de base.
        
        Args:
            db_key (str): Clé de la base de données (ex: "mongodb", "redis")
        
        Raises:
            ValueError: Si la base de données n'est pas configurée
        """
        # Récupérer la configuration
        self.config = get_database_config(db_key)
        
        if not self.config:
            raise ValueError(f"Base de données '{db_key}' non configurée dans sources.py")
        
        # Informations de base
        self.db_key = db_key.lower()
        self.name = self.config['name']
        self.category = self.config['category']
        
        # Configuration des requêtes HTTP
        self.timeout = 30  # Timeout de 30 secondes
        self.max_retries = 3  # Nombre max de tentatives
        self.retry_delay = 2  # Délai entre les retries (secondes)
        
        # Headers HTTP standards
        self.headers = {
            'User-Agent': 'VeilleNoSQL/1.0 (Educational Project USTHB)',
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8'
        }
        
        # Compteurs pour statistiques
        self.requests_count = 0
        self.success_count = 0
        self.error_count = 0
    
    
    def make_request(self, url, params=None, headers=None, method='GET'):
        """
        Faire une requête HTTP avec gestion d'erreurs et retry automatique.
        
        Args:
            url (str): URL à requêter
            params (dict, optional): Paramètres de la requête
            headers (dict, optional): Headers HTTP supplémentaires
            method (str): Méthode HTTP (GET, POST, etc.)
        
        Returns:
            requests.Response: Réponse HTTP ou None en cas d'échec
        
        Exemple:
            >>> response = self.make_request('https://api.github.com/repos/mongodb/mongo')
            >>> if response and response.status_code == 200:
            ...     data = response.json()
        """
        # Combiner les headers
        request_headers = self.headers.copy()
        if headers:
            request_headers.update(headers)
        
        # Tentatives avec retry
        for attempt in range(1, self.max_retries + 1):
            try:
                self.requests_count += 1
                
                # Log de la requête
                self._log_request(method, url, attempt)
                
                # Faire la requête
                if method.upper() == 'GET':
                    response = requests.get(
                        url,
                        params=params,
                        headers=request_headers,
                        timeout=self.timeout
                    )
                elif method.upper() == 'POST':
                    response = requests.post(
                        url,
                        params=params,
                        headers=request_headers,
                        timeout=self.timeout
                    )
                else:
                    raise ValueError(f"Méthode HTTP non supportée: {method}")
                
                # Vérifier le status code
                if response.status_code == 200:
                    self.success_count += 1
                    self._log_success(url, response)
                    return response
                
                elif response.status_code == 403:
                    # Rate limit dépassé
                    self._log_rate_limit(url)
                    return None
                
                elif response.status_code == 404:
                    # Ressource non trouvée
                    self._log_not_found(url)
                    return None
                
                elif response.status_code >= 500:
                    # Erreur serveur - on peut retry
                    self._log_server_error(url, response.status_code, attempt)
                    if attempt < self.max_retries:
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        self.error_count += 1
                        return None
                
                else:
                    # Autre erreur
                    self._log_error(url, f"Status code: {response.status_code}")
                    self.error_count += 1
                    return None
            
            except requests.exceptions.Timeout:
                self._log_timeout(url, attempt)
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    self.error_count += 1
                    return None
            
            except requests.exceptions.ConnectionError:
                self._log_connection_error(url, attempt)
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    self.error_count += 1
                    return None
            
            except Exception as e:
                self._log_error(url, str(e))
                self.error_count += 1
                return None
        
        # Si on arrive ici, toutes les tentatives ont échoué
        return None
    
    
    def sleep(self, seconds):
        """
        Attendre un certain temps (pour respecter le rate limiting).
        
        Args:
            seconds (float): Nombre de secondes à attendre
        """
        if seconds > 0:
            time.sleep(seconds)
    
    
    def create_data_entry(self, source, data_type, title, date, description, url, **kwargs):
        """
        Créer une entrée de données avec un format uniforme.
        
        Tous les scrapers doivent utiliser ce format pour garantir
        la compatibilité avec le reste du système.
        
        Args:
            source (str): Source ('github', 'blog_rss', 'nvd')
            data_type (str): Type ('release', 'blog_post', 'vulnerability')
            title (str): Titre
            date (str): Date au format YYYY-MM-DD
            description (str): Description complète
            url (str): URL vers la source
            **kwargs: Champs additionnels spécifiques
        
        Returns:
            dict: Données structurées
        
        Exemple:
            >>> entry = self.create_data_entry(
            ...     source='github',
            ...     data_type='release',
            ...     title='MongoDB 7.0.0',
            ...     date='2023-08-28',
            ...     description='New features...',
            ...     url='https://github.com/...',
            ...     version='7.0.0'
            ... )
        """
        # Structure de base
        entry = {
            'source': source,
            'database': self.name,
            'category': self.category,
            'type': data_type,
            'title': title,
            'date': date,
            'description': description,
            'url': url,
            'collected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Ajouter les champs additionnels
        entry.update(kwargs)
        
        return entry
    
    
    def get_statistics(self):
        """
        Récupérer les statistiques du scraper.
        
        Returns:
            dict: Statistiques (requêtes, succès, erreurs)
        
        Exemple:
            >>> stats = scraper.get_statistics()
            >>> print(f"Succès: {stats['success_rate']}%")
        """
        total = self.requests_count
        success_rate = (self.success_count / total * 100) if total > 0 else 0
        
        return {
            'total_requests': total,
            'successful': self.success_count,
            'errors': self.error_count,
            'success_rate': round(success_rate, 2)
        }
    
    
    # ============================================
    # MÉTHODES DE LOGGING (privées)
    # ============================================
    
    def _log_request(self, method, url, attempt):
        """Logger le début d'une requête"""
        if attempt > 1:
            print(f" [{self.name}] Tentative {attempt}/{self.max_retries}: {method} {url}")
        # Pas de log pour la première tentative (trop verbeux)
    
    
    def _log_success(self, url, response):
        """Logger une requête réussie"""
        # Pas de log pour chaque succès (trop verbeux)
        # On log seulement les stats à la fin
        pass
    
    
    def _log_error(self, url, error_msg):
        """Logger une erreur"""
        print(f" [{self.name}] Erreur: {error_msg}")
        print(f"   URL: {url}")
    
    
    def _log_timeout(self, url, attempt):
        """Logger un timeout"""
        print(f"  [{self.name}] Timeout (tentative {attempt}/{self.max_retries})")
        print(f"   URL: {url}")
    
    
    def _log_connection_error(self, url, attempt):
        """Logger une erreur de connexion"""
        print(f" [{self.name}] Erreur de connexion (tentative {attempt}/{self.max_retries})")
        print(f"   URL: {url}")
    
    
    def _log_rate_limit(self, url):
        """Logger un dépassement de rate limit"""
        print(f" [{self.name}] Rate limit dépassé!")
        print(f"   URL: {url}")
        print(f"   Conseil: Ajouter un token ou attendre")
    
    
    def _log_not_found(self, url):
        """Logger une ressource non trouvée"""
        print(f" [{self.name}] Ressource non trouvée (404)")
        print(f"   URL: {url}")
    
    
    def _log_server_error(self, url, status_code, attempt):
        """Logger une erreur serveur"""
        print(f" [{self.name}] Erreur serveur {status_code} (tentative {attempt}/{self.max_retries})")
        print(f"   URL: {url}")
    
    
    def __repr__(self):
        """Représentation string du scraper"""
        return f"<{self.__class__.__name__}(database='{self.name}', category='{self.category}')>"


# ============================================
# TESTS
# ============================================

if __name__ == "__main__":
    """
    Tests de la classe de base.
    Lance avec: python scrapers/base_scraper.py
    """
    
    print("Test de la classe BaseScraper\n")
    
    # Test 1: Initialisation
    print("Test d'initialisation:")
    try:
        scraper = BaseScraper('mongodb')
        print(f"   Scraper créé: {scraper}")
        print(f"   Database: {scraper.name}")
        print(f"   Category: {scraper.category}")
    except Exception as e:
        print(f"  Erreur: {e}")
    print()
    
    # Test 2: Requête HTTP réussie
    print(" Test de requête HTTP (GitHub API):")
    try:
        scraper = BaseScraper('mongodb')
        url = "https://api.github.com/repos/mongodb/mongo"
        response = scraper.make_request(url)
        
        if response and response.status_code == 200:
            data = response.json()
            print(f"  Requête réussie!")
            print(f"   Repo: {data['full_name']}")
            print(f"   Stars: {data['stargazers_count']}")
        else:
            print(f"  Requête échouée")
    except Exception as e:
        print(f"  Erreur: {e}")
    print()
    
    # Test 3: Format de données
    print("Test de création d'entrée de données:")
    try:
        scraper = BaseScraper('mongodb')
        entry = scraper.create_data_entry(
            source='github',
            data_type='release',
            title='MongoDB 7.0.0',
            date='2023-08-28',
            description='Major release with vector search',
            url='https://github.com/mongodb/mongo/releases/tag/r7.0.0',
            version='7.0.0'
        )
        print(f"  Entrée créée:")
        print(f"   Type: {entry['type']}")
        print(f"   Database: {entry['database']}")
        print(f"   Title: {entry['title']}")
    except Exception as e:
        print(f"  Erreur: {e}")
    print()
    
    # Test 4: Statistiques
    print("Test des statistiques:")
    try:
        scraper = BaseScraper('redis')
        # Faire quelques requêtes
        scraper.make_request("https://api.github.com/repos/redis/redis")
        time.sleep(1)
        scraper.make_request("https://api.github.com/repos/neo4j/neo4j")
        
        stats = scraper.get_statistics()
        print(f"  Statistiques:")
        print(f"   Total requêtes: {stats['total_requests']}")
        print(f"   Succès: {stats['successful']}")
        print(f"   Erreurs: {stats['errors']}")
        print(f"   Taux de succès: {stats['success_rate']}%")
    except Exception as e:
        print(f"  Erreur: {e}")
    print()
    
    # Test 5: Gestion d'erreur (URL invalide)
    print("Test de gestion d'erreur (404):")
    try:
        scraper = BaseScraper('mongodb')
        response = scraper.make_request("https://api.github.com/repos/invalid/invalid")
        if response is None:
            print(f"  Erreur correctement gérée (None retourné)")
        else:
            print(f"   Réponse inattendue: {response.status_code}")
    except Exception as e:
        print(f"  Erreur: {e}")
    print()
    
    print("Tous les tests terminés!")