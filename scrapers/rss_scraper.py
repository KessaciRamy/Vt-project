"""
RSS Scraper - Collecte les articles de blog via flux RSS

Ce scraper récupère les articles de blog officiels des bases de données
en lisant leurs flux RSS.
"""

import sys
import os

# Fix PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import feedparser
import re
from datetime import datetime
from scrapers.base_scraper import BaseScraper
from config.sources import get_rss_url


class RSSScraper(BaseScraper):
    """
    Scraper pour collecter les articles de blog via RSS.
    
    Utilise feedparser pour lire les flux RSS des blogs officiels
    des bases de données.
    """
    
    def __init__(self, db_key):
        """
        Initialiser le RSS Scraper.
        
        Args:
            db_key (str): Clé de la base de données (ex: "mongodb")
        
        Exemple:
            >>> scraper = RSSScraper('mongodb')
        """
        # Appeler le constructeur parent
        super().__init__(db_key)
        
        # Récupérer l'URL RSS depuis la config
        self.rss_url = get_rss_url(db_key)
        
        if not self.rss_url:
            raise ValueError(f"Pas de flux RSS configuré pour '{db_key}'")
        
        print(f"✅ [{self.name}] RSS configuré: {self.rss_url}")
    
    
    def get_blog_posts(self, limit=10):
        """
        Récupérer les articles de blog depuis le flux RSS.
        
        Args:
            limit (int): Nombre maximum d'articles à récupérer
        
        Returns:
            list: Liste de dictionnaires contenant les articles
        
        Exemple:
            >>> scraper = RSSScraper('mongodb')
            >>> posts = scraper.get_blog_posts(limit=5)
            >>> print(f"Trouvé {len(posts)} articles")
        """
        # Log
        print(f"🔍 [{self.name}] Collecte des articles depuis RSS...")
        print(f"   URL: {self.rss_url}")
        
        # Parser le flux RSS avec feedparser
        try:
            feed = feedparser.parse(self.rss_url)
        except Exception as e:
            print(f"❌ [{self.name}] Erreur de parsing du flux RSS: {e}")
            return []
        
        # Vérifier que le flux est valide
        if feed.bozo:  # bozo = 1 si erreur de parsing
            print(f"⚠️  [{self.name}] Flux RSS mal formé (bozo)")
            # On continue quand même, parfois ça marche
        
        # Vérifier qu'il y a des entrées
        if not feed.entries:
            print(f"⚠️  [{self.name}] Aucun article trouvé dans le flux RSS")
            return []
        
        # Traiter les articles
        posts = []
        for entry in feed.entries[:limit]:
            try:
                # Extraire les informations
                processed_post = self._process_entry(entry)
                if processed_post:
                    posts.append(processed_post)
            except Exception as e:
                print(f"⚠️  [{self.name}] Erreur sur un article: {e}")
                continue
        
        print(f"✅ [{self.name}] {len(posts)} articles collectés")
        
        return posts
    
    
    def _process_entry(self, entry):
        """
        Traiter une entrée RSS et extraire les infos importantes.
        
        Args:
            entry: Entrée feedparser
        
        Returns:
            dict: Données structurées de l'article
        """
        # Extraire les champs de base
        title = entry.get('title', 'Sans titre')
        link = entry.get('link', '')
        
        # Description/résumé (peut être dans summary ou description)
        summary = entry.get('summary', entry.get('description', ''))
        
        # Date de publication (plusieurs formats possibles)
        published = entry.get('published', entry.get('updated', ''))
        
        # Auteur (optionnel)
        author = entry.get('author', '')
        
        # Tags/catégories (optionnel)
        tags = []
        if hasattr(entry, 'tags'):
            tags = [tag.term for tag in entry.tags]
        
        # Nettoyer la description (enlever HTML)
        description = self._clean_html(summary)
        
        # Normaliser la date
        date = self._normalize_date(published)
        
        # Créer l'entrée avec le format uniforme
        entry_data = self.create_data_entry(
            source='blog_rss',
            data_type='blog_post',
            title=title,
            date=date,
            description=description,
            url=link,
            # Champs spécifiques aux articles de blog
            author=author,
            tags=tags
        )
        
        return entry_data
    
    
    def _clean_html(self, html_text):
        """
        Nettoyer le HTML d'une description.
        
        Args:
            html_text (str): Texte avec balises HTML
        
        Returns:
            str: Texte propre sans HTML
        """
        if not html_text:
            return "Pas de description disponible"
        
        # Enlever les balises HTML avec regex
        text = re.sub(r'<[^>]+>', '', html_text)
        
        # Enlever les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
        # Enlever les entités HTML courantes
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        
        # Nettoyer et tronquer
        text = text.strip()
        
        # Tronquer si trop long (garder 1000 caractères)
        if len(text) > 1000:
            text = text[:997] + "..."
        
        return text or "Pas de description disponible"
    
    
    def _normalize_date(self, date_string):
        """
        Normaliser une date au format YYYY-MM-DD.
        
        Args:
            date_string (str): Date dans n'importe quel format
        
        Returns:
            str: Date normalisée (ex: "2023-08-28")
        """
        if not date_string:
            return datetime.now().strftime('%Y-%m-%d')
        
        try:
            # feedparser parse automatiquement les dates
            # On utilise dateutil pour plus de flexibilité
            from dateutil import parser
            dt = parser.parse(date_string)
            return dt.strftime('%Y-%m-%d')
        except Exception:
            # Si échec, retourner la date actuelle
            return datetime.now().strftime('%Y-%m-%d')
    
    
    def get_latest_post(self):
        """
        Récupérer uniquement le dernier article.
        
        Returns:
            dict: Dernier article ou None
        
        Exemple:
            >>> scraper = RSSScraper('mongodb')
            >>> latest = scraper.get_latest_post()
            >>> print(f"Dernier article: {latest['title']}")
        """
        posts = self.get_blog_posts(limit=1)
        return posts[0] if posts else None
    
    
    def get_feed_info(self):
        """
        Récupérer les informations générales du flux RSS.
        
        Returns:
            dict: Informations sur le flux (titre, description, etc.)
        
        Exemple:
            >>> scraper = RSSScraper('mongodb')
            >>> info = scraper.get_feed_info()
            >>> print(f"Blog: {info['title']}")
        """
        try:
            feed = feedparser.parse(self.rss_url)
            
            return {
                'title': feed.feed.get('title', 'Unknown'),
                'description': feed.feed.get('description', ''),
                'link': feed.feed.get('link', ''),
                'total_entries': len(feed.entries)
            }
        except Exception as e:
            print(f"❌ Erreur récupération info flux: {e}")
            return None


# ============================================
# TESTS
# ============================================

if __name__ == "__main__":
    """
    Tests du RSS Scraper.
    Lance avec: python -m scrapers.rss_scraper
    """
    
    print("\n" + "="*60)
    print("🧪 TEST DU RSS SCRAPER")
    print("="*60 + "\n")
    
    # Test 1: Initialisation
    print("1️⃣ Test d'initialisation")
    print("-" * 60)
    try:
        scraper = RSSScraper('mongodb')
        print(f"✅ RSS Scraper créé pour {scraper.name}")
        print(f"   URL RSS: {scraper.rss_url}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        exit(1)
    print()
    
    # Test 2: Informations du flux
    print("2️⃣ Test des informations du flux RSS")
    print("-" * 60)
    try:
        info = scraper.get_feed_info()
        
        if info:
            print(f"✅ Flux RSS:")
            print(f"   Titre: {info['title']}")
            print(f"   Total d'articles: {info['total_entries']}")
            print(f"   URL: {info['link']}")
        else:
            print("⚠️  Impossible de récupérer les infos du flux")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    print()
    
    # Test 3: Récupération des articles
    print("3️⃣ Test de récupération des articles")
    print("-" * 60)
    try:
        posts = scraper.get_blog_posts(limit=3)
        
        if posts:
            print(f"✅ {len(posts)} articles récupérés\n")
            
            # Afficher les détails du premier article
            latest = posts[0]
            print("   Dernier article:")
            print(f"   📰 Titre: {latest['title']}")
            print(f"   📅 Date: {latest['date']}")
            print(f"   👤 Auteur: {latest.get('author', 'Non spécifié')}")
            print(f"   🔗 URL: {latest['url']}")
            print(f"   📄 Description: {latest['description'][:100]}...")
            if latest.get('tags'):
                print(f"   🏷️  Tags: {', '.join(latest['tags'][:3])}")
        else:
            print("⚠️  Aucun article trouvé")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    print()
    
    # Test 4: Dernier article uniquement
    print("4️⃣ Test de récupération du dernier article")
    print("-" * 60)
    try:
        latest = scraper.get_latest_post()
        
        if latest:
            print(f"✅ Dernier article: {latest['title']}")
            print(f"   Publié le: {latest['date']}")
        else:
            print("⚠️  Aucun article trouvé")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    print()
    
    # Test 5: Test avec une autre BDD (Redis)
    print("5️⃣ Test avec Redis")
    print("-" * 60)
    try:
        redis_scraper = RSSScraper('redis')
        redis_posts = redis_scraper.get_blog_posts(limit=2)
        
        if redis_posts:
            print(f"✅ {len(redis_posts)} articles Redis collectés")
            print(f"   Dernier: {redis_posts[0]['title']}")
        else:
            print("⚠️  Aucun article Redis trouvé")
    except Exception as e:
        print(f"⚠️  Redis: {e}")
    print()
    
    # Test 6: Statistiques
    print("6️⃣ Statistiques")
    print("-" * 60)
    stats = scraper.get_statistics()
    print(f"   Total requêtes: {stats['total_requests']}")
    print(f"   Succès: {stats['successful']}")
    print(f"   Erreurs: {stats['errors']}")
    print(f"   Taux de succès: {stats['success_rate']}%")
    print()
    
    print("="*60)
    print("✅ TESTS RSS SCRAPER TERMINÉS")
    print("="*60 + "\n")