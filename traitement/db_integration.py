"""
Module d'intégration PostgreSQL.

Ce module gère l'insertion des données nettoyées dans PostgreSQL
avec gestion des conflits (UPSERT) et logging des erreurs.
"""

import json
import psycopg2
from psycopg2.extras import execute_values, Json
from psycopg2 import sql
from typing import List, Dict, Any
from datetime import datetime
import configparser


class DatabaseIntegrator:
    """
    Intégrateur pour insérer les données dans PostgreSQL.
    """
    
    def __init__(self, db_config: Dict[str, str]):
        """
        Initialiser l'intégrateur.
        
        Args:
            db_config: Configuration de connexion PostgreSQL
                {
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'veille_nosql',
                    'user': 'postgres',
                    'password': 'password'
                }
        """
        self.db_config = db_config
        self.conn = None
        self.cursor = None
        
        self.stats = {
            'databases_inserted': 0,
            'releases_inserted': 0,
            'releases_updated': 0,
            'blog_posts_inserted': 0,
            'blog_posts_updated': 0,
            'vulnerabilities_inserted': 0,
            'vulnerabilities_updated': 0,
            'keywords_inserted': 0,
            'errors': []
        }
        
        print("\n" + "="*70)
        print("🗄️  INTÉGRATEUR POSTGRESQL")
        print("="*70 + "\n")
    
    def connect(self):
        """Établir la connexion à PostgreSQL"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            print(f"✅ Connecté à PostgreSQL: {self.db_config['database']}")
            return True
        
        except psycopg2.Error as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    def disconnect(self):
        """Fermer la connexion"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("\n✅ Connexion fermée")
    
    def create_tables(self):
        """Créer les tables si elles n'existent pas"""
        print("\n📋 Création des tables...")
        
        # Table: databases
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS databases (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                category VARCHAR(50) NOT NULL,
                official_site VARCHAR(255),
                github_url VARCHAR(255),
                rss_url VARCHAR(255),
                last_scraped TIMESTAMP,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Table: releases
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS releases (
                id SERIAL PRIMARY KEY,
                database_id INTEGER REFERENCES databases(id) ON DELETE CASCADE,
                version VARCHAR(50) NOT NULL,
                version_major INTEGER,
                version_minor INTEGER,
                version_patch INTEGER,
                version_prerelease VARCHAR(50),
                title TEXT NOT NULL,
                description TEXT,
                release_date DATE NOT NULL,
                url VARCHAR(500) NOT NULL,
                tag_name VARCHAR(100),
                is_prerelease BOOLEAN DEFAULT false,
                is_draft BOOLEAN DEFAULT false,
                release_type VARCHAR(20),
                has_breaking_changes BOOLEAN DEFAULT false,
                features TEXT[],
                collected_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(database_id, version)
            )
        """)
        
        # Table: blog_posts
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS blog_posts (
                id SERIAL PRIMARY KEY,
                database_id INTEGER REFERENCES databases(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                description TEXT,
                published_date DATE NOT NULL,
                url VARCHAR(500) NOT NULL UNIQUE,
                author VARCHAR(200),
                tags TEXT[],
                category VARCHAR(50),
                technical_level VARCHAR(20),
                technical_keywords TEXT[],
                collected_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Table: vulnerabilities
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS vulnerabilities (
                id SERIAL PRIMARY KEY,
                database_id INTEGER REFERENCES databases(id) ON DELETE CASCADE,
                cve_id VARCHAR(50) NOT NULL UNIQUE,
                title TEXT,
                description TEXT,
                severity VARCHAR(20) NOT NULL,
                cvss_score DECIMAL(3,1) CHECK (cvss_score >= 0 AND cvss_score <= 10),
                published_date DATE NOT NULL,
                modified_date DATE,
                url VARCHAR(500),
                is_critical BOOLEAN DEFAULT false,
                affected_versions TEXT,
                cwe_id VARCHAR(50),
                impact_type VARCHAR(50),
                patch_available BOOLEAN DEFAULT false,
                collected_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Table: keywords
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS keywords (
                id SERIAL PRIMARY KEY,
                keyword VARCHAR(100) NOT NULL,
                database_id INTEGER REFERENCES databases(id) ON DELETE CASCADE,
                category VARCHAR(50),
                occurrences INTEGER DEFAULT 1,
                UNIQUE(keyword, database_id)
            )
        """)
        
        # Index pour performance
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_releases_date 
            ON releases(release_date DESC)
        """)
        
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cve_severity 
            ON vulnerabilities(severity, cvss_score DESC)
        """)
        
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_blog_date 
            ON blog_posts(published_date DESC)
        """)
        
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_db_category 
            ON databases(category)
        """)
        
        self.conn.commit()
        print("✅ Tables créées/vérifiées")
    
    def integrate_all(self, cleaned_data: List[Dict]):
        """
        Intégrer toutes les données.
        
        Args:
            cleaned_data: Liste des données nettoyées
        """
        if not self.conn:
            print("❌ Pas de connexion à la base de données")
            return
        
        print("\n🔄 Début de l'intégration...\n")
        
        # 1. Insérer/mettre à jour les databases
        self._integrate_databases(cleaned_data)
        
        # 2. Récupérer les IDs des databases
        db_ids = self._get_database_ids()
        
        # 3. Intégrer par type
        for item in cleaned_data:
            try:
                item_type = item['type']
                db_id = db_ids.get(item['database'])
                
                if not db_id:
                    self._log_error(item, "Database ID non trouvé")
                    continue
                
                if item_type == 'release':
                    self._insert_release(item, db_id)
                elif item_type == 'blog_post':
                    self._insert_blog_post(item, db_id)
                elif item_type == 'vulnerability':
                    self._insert_vulnerability(item, db_id)
                
                # Extraire et insérer les keywords
                self._insert_keywords(item, db_id)
            
            except Exception as e:
                self._log_error(item, str(e))
        
        # Commit final
        self.conn.commit()
        
        # Afficher le résumé
        self._print_summary()
    
    def _integrate_databases(self, data: List[Dict]):
        """Insérer/mettre à jour les databases"""
        print("1️⃣ Intégration des databases...")
        
        # Extraire les databases uniques
        databases = {}
        for item in data:
            db_name = item['database']
            if db_name not in databases:
                databases[db_name] = item['category']
        
        # Insérer avec UPSERT
        for db_name, category in databases.items():
            self.cursor.execute("""
                INSERT INTO databases (name, category, last_scraped)
                VALUES (%s, %s, NOW())
                ON CONFLICT (name) 
                DO UPDATE SET 
                    last_scraped = NOW(),
                    category = EXCLUDED.category
            """, (db_name, category))
            
            self.stats['databases_inserted'] += 1
        
        self.conn.commit()
        print(f"   ✅ {len(databases)} databases intégrées")
    
    def _get_database_ids(self) -> Dict[str, int]:
        """Récupérer les IDs des databases"""
        self.cursor.execute("SELECT name, id FROM databases")
        return {row[0]: row[1] for row in self.cursor.fetchall()}
    
    def _insert_release(self, item: Dict, db_id: int):
        """Insérer une release (avec UPSERT)"""
        try:
            self.cursor.execute("""
                INSERT INTO releases (
                    database_id, version, version_major, version_minor, version_patch,
                    version_prerelease, title, description, release_date, url, tag_name,
                    is_prerelease, is_draft, release_type, has_breaking_changes, features
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (database_id, version)
                DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    release_date = EXCLUDED.release_date,
                    url = EXCLUDED.url,
                    release_type = EXCLUDED.release_type,
                    has_breaking_changes = EXCLUDED.has_breaking_changes,
                    features = EXCLUDED.features
                RETURNING (xmax = 0) AS inserted
            """, (
                db_id,
                item.get('version_clean', item.get('version')),
                item.get('version_major'),
                item.get('version_minor'),
                item.get('version_patch'),
                item.get('version_prerelease'),
                item['title'],
                item.get('description'),
                item['date'],
                item['url'],
                item.get('tag_name'),
                item.get('is_prerelease', False),
                item.get('is_draft', False),
                item.get('release_type', 'unknown'),
                item.get('has_breaking_changes', False),
                item.get('features', [])
            ))
            
            inserted = self.cursor.fetchone()[0]
            if inserted:
                self.stats['releases_inserted'] += 1
            else:
                self.stats['releases_updated'] += 1
        
        except psycopg2.Error as e:
            self._log_error(item, f"Release insert error: {e}")
    
    def _insert_blog_post(self, item: Dict, db_id: int):
        """Insérer un article de blog (avec UPSERT)"""
        try:
            self.cursor.execute("""
                INSERT INTO blog_posts (
                    database_id, title, description, published_date, url,
                    author, tags, category, technical_level, technical_keywords
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (url)
                DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    category = EXCLUDED.category,
                    technical_level = EXCLUDED.technical_level,
                    technical_keywords = EXCLUDED.technical_keywords
                RETURNING (xmax = 0) AS inserted
            """, (
                db_id,
                item['title'],
                item.get('description'),
                item['date'],
                item['url'],
                item.get('author'),
                item.get('tags', []),
                item.get('category', 'general'),
                item.get('technical_level', 'intermediate'),
                item.get('technical_keywords', [])
            ))
            
            inserted = self.cursor.fetchone()[0]
            if inserted:
                self.stats['blog_posts_inserted'] += 1
            else:
                self.stats['blog_posts_updated'] += 1
        
        except psycopg2.Error as e:
            self._log_error(item, f"Blog post insert error: {e}")
    
    def _insert_vulnerability(self, item: Dict, db_id: int):
        """Insérer une vulnérabilité (avec UPSERT)"""
        try:
            self.cursor.execute("""
                INSERT INTO vulnerabilities (
                    database_id, cve_id, title, description, severity, cvss_score,
                    published_date, modified_date, url, is_critical, affected_versions,
                    cwe_id, impact_type, patch_available
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (cve_id)
                DO UPDATE SET
                    description = EXCLUDED.description,
                    modified_date = EXCLUDED.modified_date,
                    affected_versions = EXCLUDED.affected_versions,
                    patch_available = EXCLUDED.patch_available
                RETURNING (xmax = 0) AS inserted
            """, (
                db_id,
                item['cve_id'],
                item.get('title', item['cve_id']),
                item.get('description'),
                item['severity'],
                item['cvss_score'],
                item.get('published_date', item['date']),
                item.get('modified_date'),
                item['url'],
                item.get('is_critical', False),
                item.get('affected_versions', 'Unknown'),
                item.get('cwe_id'),
                item.get('impact_type', 'other'),
                item.get('patch_available', False)
            ))
            
            inserted = self.cursor.fetchone()[0]
            if inserted:
                self.stats['vulnerabilities_inserted'] += 1
            else:
                self.stats['vulnerabilities_updated'] += 1
        
        except psycopg2.Error as e:
            self._log_error(item, f"Vulnerability insert error: {e}")
    
    def _insert_keywords(self, item: Dict, db_id: int):
        """Insérer les mots-clés"""
        keywords = []
        
        # Collecter les keywords selon le type
        if item['type'] == 'blog_post':
            keywords = item.get('technical_keywords', [])
        elif item['type'] == 'release':
            # Extraire des mots-clés des features
            for feature in item.get('features', [])[:5]:
                words = feature.split()[:3]  # Premiers mots
                keywords.extend(words)
        
        # Insérer chaque keyword
        for keyword in keywords[:10]:  # Max 10 par item
            if len(keyword) > 3:  # Ignorer mots trop courts
                try:
                    self.cursor.execute("""
                        INSERT INTO keywords (keyword, database_id, category)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (keyword, database_id)
                        DO UPDATE SET occurrences = keywords.occurrences + 1
                    """, (keyword.lower(), db_id, item['type']))
                    
                    self.stats['keywords_inserted'] += 1
                except:
                    pass  # Ignorer erreurs keywords
    
    def _log_error(self, item: Dict, message: str):
        """Logger une erreur"""
        error = {
            'database': item.get('database', 'Unknown'),
            'type': item.get('type', 'Unknown'),
            'title': item.get('title', item.get('cve_id', 'No title'))[:50],
            'error': message
        }
        self.stats['errors'].append(error)
    
    def _print_summary(self):
        """Afficher le résumé de l'intégration"""
        print("\n" + "="*70)
        print("📊 RÉSUMÉ DE L'INTÉGRATION")
        print("="*70)
        print(f"   Databases         : {self.stats['databases_inserted']}")
        print(f"   Releases          : {self.stats['releases_inserted']} insérées, "
              f"{self.stats['releases_updated']} mises à jour")
        print(f"   Articles          : {self.stats['blog_posts_inserted']} insérés, "
              f"{self.stats['blog_posts_updated']} mis à jour")
        print(f"   Vulnérabilités    : {self.stats['vulnerabilities_inserted']} insérées, "
              f"{self.stats['vulnerabilities_updated']} mises à jour")
        print(f"   Mots-clés         : {self.stats['keywords_inserted']}")
        
        total_ops = (self.stats['releases_inserted'] + self.stats['releases_updated'] +
                     self.stats['blog_posts_inserted'] + self.stats['blog_posts_updated'] +
                     self.stats['vulnerabilities_inserted'] + self.stats['vulnerabilities_updated'])
        
        print(f"\n   Total opérations  : {total_ops}")
        
        if self.stats['errors']:
            print(f"\n   ⚠️  Erreurs ({len(self.stats['errors'])}):")
            for error in self.stats['errors'][:5]:
                print(f"      - [{error['database']}] {error['error'][:60]}")
            if len(self.stats['errors']) > 5:
                print(f"      ... et {len(self.stats['errors']) - 5} autres")
        
        print("="*70 + "\n")


# ==========================================
# FONCTION PRINCIPALE
# ==========================================

def main():
    """Fonction principale d'intégration"""
    
    print("\n" + "="*70)
    print("🚀 INTÉGRATION POSTGRESQL - VEILLE NOSQL/NEWSQL")
    print("="*70 + "\n")
    
    # Configuration de la base de données
    config = configparser.ConfigParser()
    config.read('database.ini') # Lit votre fichier database.ini
    
    if 'postgresql' in config:
        # Récupère les paramètres de la section [postgresql]
        DB_CONFIG = dict(config['postgresql'])
        print("📂 Configuration chargée depuis database.ini")
    else:
        print("❌ Erreur: Section [postgresql] non trouvée dans database.ini")
        return
    
    # Charger les données nettoyées
    print("📂 Chargement des données nettoyées...")
    try:
        with open('cleaned_data.json', 'r', encoding='utf-8') as f:
            cleaned_data = json.load(f)
        print(f"✅ {len(cleaned_data)} éléments chargés\n")
    except FileNotFoundError:
        print("❌ Fichier cleaned_data.json non trouvé!")
        print("   Lancez d'abord: python data_processor.py")
        return
    
    # Créer l'intégrateur
    integrator = DatabaseIntegrator(DB_CONFIG)
    
    # Se connecter
    if not integrator.connect():
        print("❌ Impossible de se connecter à PostgreSQL")
        return
    
    try:
        # Créer les tables
        integrator.create_tables()
        
        # Intégrer les données
        integrator.integrate_all(cleaned_data)
        
        print("\n✅ Intégration terminée avec succès!")
    
    except Exception as e:
        print(f"\n❌ Erreur lors de l'intégration: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Fermer la connexion
        integrator.disconnect()


if __name__ == "__main__":
    main()
