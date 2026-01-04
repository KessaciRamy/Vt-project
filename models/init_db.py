import psycopg2
from models.db_connection import get_connection

def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    # Table: users
    cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                compte VARCHAR(50) PRIMARY KEY UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                user_type VARCHAR(20) NOT NULL CHECK (user_type IN ('veilleur', 'analyste', 'decideur'))
                )
                """)
    
    # Table: databases
    cur.execute("""
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
    cur.execute("""
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
    cur.execute("""
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
    cur.execute("""
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
    cur.execute("""
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
    cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_releases_date 
            ON releases(release_date DESC)
    """)
        
    cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_cve_severity 
            ON vulnerabilities(severity, cvss_score DESC)
    """)
        
    cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_blog_date 
            ON blog_posts(published_date DESC)
    """)
        
    cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_db_category 
            ON databases(category)
    """)

    conn.commit()
    cur.close()
    conn.close()