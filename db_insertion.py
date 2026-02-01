import json
import psycopg2
from typing import Dict

class DatabaseIngestor:
    def __init__(self, db_config: dict):
        self.conn = psycopg2.connect(**db_config)
        self.cursor = self.conn.cursor()

        self.stats = {
            "databases_created": 0,
            "releases_inserted": 0,
            "blog_posts_inserted": 0,
            "vulnerabilities_inserted": 0,
            "keywords_inserted": 0,
            "keywords_errors": 0,
            "skipped": 0
        }

        print("🧠 DB USED:", self.conn.get_dsn_parameters())
    # -------------------------------------------------
    # DATABASES
    # -------------------------------------------------
    def get_or_create_database(self, name: str, category: str ):
        self.cursor.execute("""
            INSERT INTO databases (name, category)
            VALUES (%s, %s)
            ON CONFLICT (name) DO NOTHING
            RETURNING id
        """, (name, category))

        row = self.cursor.fetchone()
        if row:
            self.stats["databases_created"] += 1
            return row[0]

        self.cursor.execute("SELECT id FROM databases WHERE name=%s", (name,))
        return self.cursor.fetchone()[0]
    def update_database_category(self, db_id: int, category: str):
        self.cursor.execute("""
        UPDATE databases
        SET category = %s
        WHERE id = %s
          AND (category IS NULL OR category = '')
        """, (category, db_id))
    # -------------------------------------------------
    # RELEASES
    # -------------------------------------------------
    def insert_release(self, db_id: int, item: dict):
        self.cursor.execute("""
            INSERT INTO releases (
                database_id, version, version_major, version_minor,
                version_patch, version_prerelease,
                title, description, release_date, url,
                release_type, has_breaking_changes, features
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (database_id, version) DO NOTHING
        """, (
            db_id,
            item.get("version_clean"),
            item.get("version_major"),
            item.get("version_minor"),
            item.get("version_patch"),
            item.get("version_prerelease"),
            item.get("title"),
            item.get("description"),
            item.get("date"),
            item.get("url"),
            item.get("release_type"),
            item.get("has_breaking_changes", False),
            item.get("features", [])
        ))

        if self.cursor.rowcount:
            self.stats["releases_inserted"] += 1
        else:
            self.stats["skipped"] += 1

    # -------------------------------------------------
    # BLOG POSTS
    # -------------------------------------------------
    def insert_blog_post(self, db_id: int, item: dict):
        self.cursor.execute("""
            INSERT INTO blog_posts (
                database_id, title, description,
                published_date, url,
                category, technical_level, technical_keywords
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (url) DO NOTHING
        """, (
            db_id,
            item.get("title"),
            item.get("description"),
            item.get("date"),
            item.get("url"),
            item.get("category"),
            item.get("technical_level"),
            item.get("technical_keywords", [])
        ))

        if self.cursor.rowcount:
            self.stats["blog_posts_inserted"] += 1
        else:
            self.stats["skipped"] += 1

    # -------------------------------------------------
    # VULNERABILITIES
    # -------------------------------------------------
    def insert_vulnerability(self, db_id: int, item: dict):
        self.cursor.execute("""
            INSERT INTO vulnerabilities (
                database_id, cve_id, title, description,
                severity, cvss_score,
                published_date, modified_date,
                url, is_critical,
                affected_versions, cwe_id,
                impact_type, patch_available
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (cve_id) DO NOTHING
        """, (
            db_id,
            item.get("cve_id"),
            item.get("title"),
            item.get("description"),
            item.get("severity"),
            item.get("cvss_score"),
            item.get("published_date"),
            item.get("modified_date"),
            item.get("url"),
            item.get("cvss_score", 0) >= 9,
            item.get("affected_versions"),
            item.get("cwe_id"),
            item.get("impact_type"),
            item.get("patch_available", False)
        ))

        if self.cursor.rowcount:
            self.stats["vulnerabilities_inserted"] += 1
        else:
            self.stats["skipped"] += 1


    # -------------------------------------------------
    # KEYWORDS
    # -------------------------------------------------

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
                except Exception as e:
                    self.stats['keywords_errors'] += 1
    # -------------------------------------------------
    # MAIN INGESTION
    # -------------------------------------------------
    def ingest(self, cleaned_json_path: str):
        with open(cleaned_json_path, encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            print("➡️ Processing item:", item["type"], item.get("database"))
            db_name = item["database"]
            db_id = self.get_or_create_database(db_name, category="")

            if item.get("source") == "nvd" and item.get("category"):
                self.update_database_category(db_id, item["category"])

            if item["type"] == "release":
                self.insert_release(db_id, item)
                self._insert_keywords(item, db_id)

            elif item["type"] == "blog_post":
                self.insert_blog_post(db_id, item)
                self._insert_keywords(item, db_id)

            elif item["type"] == "vulnerability":
                self.insert_vulnerability(db_id, item)

        self.conn.commit()
        print("✅ COMMIT DONE")
        return self.stats

    def close(self):
        self.cursor.close()
        self.conn.close()