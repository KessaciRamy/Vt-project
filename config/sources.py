"""
Configuration des sources de données pour la veille technologique NoSQL/NewSQL

Ce fichier contient toutes les informations nécessaires pour collecter
les données depuis différentes sources (GitHub, RSS, NVD) pour chaque base de données.
"""

# ============================================
# CONFIGURATION DE TOUTES LES BASES DE DONNÉES
# ============================================

DATABASES_CONFIG = {
    "mongodb": {
        "name": "MongoDB",
        "category": "Document Store",
        "github": {
            "owner": "mongodb",
            "repo": "mongo",
            "url": "https://github.com/mongodb/mongo"
        },
        "blog": {
            "url": "https://www.mongodb.com/blog",
            "rss": "https://www.mongodb.com/blog/rss.xml"
        },
        "website": "https://www.mongodb.com",
        "docs": "https://www.mongodb.com/docs/manual/release-notes/",
        "keywords": ["mongodb", "mongo"]  # Pour recherche CVE dans NVD
    },
    
    "redis": {
        "name": "Redis",
        "category": "Key-Value",
        "github": {
            "owner": "redis",
            "repo": "redis",
            "url": "https://github.com/redis/redis"
        },
        "blog": {
            "url": "https://redis.io/blog/",
            "rss": "https://redis.io/blog/rss.xml"
        },
        "website": "https://redis.io",
        "docs": "https://redis.io/docs/about/releases/",
        "keywords": ["redis"]
    },
    
    "neo4j": {
        "name": "Neo4j",
        "category": "Graph",
        "github": {
            "owner": "neo4j",
            "repo": "neo4j",
            "url": "https://github.com/neo4j/neo4j"
        },
        "blog": {
            "url": "https://neo4j.com/blog/",
            "rss": "https://neo4j.com/feed/"
        },
        "website": "https://neo4j.com",
        "docs": "https://neo4j.com/release-notes/",
        "keywords": ["neo4j"]
    },

    "cassandra": {
        "name": "Apache Cassandra",
        "category": "Columnar",
        "github": {
            "owner": "apache",
            "repo": "cassandra",
            "url": "https://github.com/apache/cassandra"
        },
        "blog": {
            "url": "https://cassandra.apache.org/blog/",
            "rss": "https://cassandra.apache.org/_/feed.xml"
        },
        "website": "https://cassandra.apache.org",
        "keywords": ["cassandra", "apache cassandra"]
    },

    "elasticsearch": {
        "name": "Elasticsearch",
        "category": "Search Engine",
        "github": {
            "owner": "elastic",
            "repo": "elasticsearch",
            "url": "https://github.com/elastic/elasticsearch"
        },
        "blog": {
            "url": "https://www.elastic.co/blog/",
            "rss": "https://www.elastic.co/blog/feed"
        },
        "website": "https://www.elastic.co/elasticsearch/",
        "keywords": ["elasticsearch", "elastic"]
    },
    
    "influxdb": {
        "name": "InfluxDB",
        "category": "Time Series",
        "github": {
            "owner": "influxdata",
            "repo": "influxdb",
            "url": "https://github.com/influxdata/influxdb"
       },
       "blog": {
            "url": "https://www.influxdata.com/blog/",
            "rss": "https://www.influxdata.com/feed/"
        },
        "website": "https://www.influxdata.com/",
        "keywords": ["influxdb", "influx"]
    },

    "cockroachdb": {
        "name": "CockroachDB",
        "category": "Distributed SQL",
        "github": {
            "owner": "cockroachdb",
            "repo": "cockroach",
            "url": "https://github.com/cockroachdb/cockroach"
        },
        "blog": {
            "url": "https://www.cockroachlabs.com/blog/",
            "rss": "https://www.cockroachlabs.com/blog/feed/"
        },
        "website": "https://www.cockroachlabs.com",
        "docs": "https://www.cockroachlabs.com/docs/releases/",
        "keywords": ["cockroachdb", "cockroach"]
    },
    
   "postgresql": {
        "name": "PostgreSQL",
        "category": "Relational SQL",
        "github": {
            "owner": "postgres",
            "repo": "postgres",
            "url": "https://github.com/postgres/postgres"
        },
        "blog": {
            "url": "https://www.postgresql.org/about/news/",
            "rss": "https://www.postgresql.org/news.rss"
        },
        "website": "https://www.postgresql.org",
        "docs": "https://www.postgresql.org/docs/release/",
        "keywords": ["postgresql", "postgres"]
    },

    "mysql": {
        "name": "MySQL",
        "category": "Relational SQL",
        "github": {
            "owner": "mysql",
            "repo": "mysql-server",
            "url": "https://github.com/mysql/mysql-server"
        },
        "blog": {
            "url": "https://blogs.oracle.com/mysql/",
            "rss": "https://blogs.oracle.com/mysql/rss"
       },
       "website": "https://www.mysql.com",
       "keywords": ["mysql"]
    },

    "mariadb": {
    "name": "MariaDB",
    "category": "Relational SQL",
    "github": {
        "owner": "MariaDB",
        "repo": "server",
        "url": "https://github.com/MariaDB/server"
    },
    "blog": {
        "url": "https://mariadb.com/resources/blog/",
        "rss": "https://mariadb.com/feed/"
    },
    "website": "https://mariadb.org",
    "keywords": ["mariadb"]
    },

    "couchdb": {
    "name": "Apache CouchDB",
    "category": "Document Store",
    "github": {
        "owner": "apache",
        "repo": "couchdb",
        "url": "https://github.com/apache/couchdb"
    },
    "blog": {
        "url": "https://blog.couchdb.org/",
        "rss": "https://blog.couchdb.org/feed.xml"
    },
    "website": "https://couchdb.apache.org",
    "keywords": ["couchdb", "apache couchdb"]
    },

    "arangodb": {
    "name": "ArangoDB",
    "category": "Multi-Model",
    "github": {
        "owner": "arangodb",
        "repo": "arangodb",
        "url": "https://github.com/arangodb/arangodb"
    },
    "blog": {
        "url": "https://www.arangodb.com/blog/",
        "rss": "https://www.arangodb.com/feed/"
    },
    "website": "https://www.arangodb.com",
    "keywords": ["arangodb", "arango"]
    },

    "memcached": {
    "name": "Memcached",
    "category": "Key-Value",
    "github": {
        "owner": "memcached",
        "repo": "memcached",
        "url": "https://github.com/memcached/memcached"
    },
    "blog": {
        "url": "https://memcached.org/blog/",
        "rss": "https://memcached.org/blog/feed/"
    },
    "website": "https://memcached.org",
    "keywords": ["memcached"]
    },

    "rethinkdb": {
    "name": "RethinkDB",
    "category": "Document Store",
    "github": {
        "owner": "rethinkdb",
        "repo": "rethinkdb",
        "url": "https://github.com/rethinkdb/rethinkdb"
    },
    "blog": {
        "url": "https://rethinkdb.com/blog/",
        "rss": "https://rethinkdb.com/blog/feed/"
    },
    "website": "https://rethinkdb.com",
    "keywords": ["rethinkdb"]
    },

    "hbase": {
    "name": "Apache HBase",
    "category": "Columnar",
    "github": {
        "owner": "apache",
        "repo": "hbase",
        "url": "https://github.com/apache/hbase"
    },
    "blog": {
        "url": "https://hbase.apache.org/blog/",
        "rss": "https://blogs.apache.org/hbase/feed/entries/rss"
    },
    "website": "https://hbase.apache.org",
    "keywords": ["hbase", "apache hbase"]
    },

    "solr": {
    "name": "Apache Solr",
    "category": "Search Engine",
    "github": {
        "owner": "apache",
        "repo": "solr",
        "url": "https://github.com/apache/solr"
    },
    "blog": {
        "url": "https://solr.apache.org/blog/",
        "rss": "https://blogs.apache.org/solr/feed/entries/rss"
    },
    "website": "https://solr.apache.org",
    "keywords": ["solr", "apache solr"]
    },

    "tidb": {
    "name": "TiDB",
    "category": "Distributed SQL",
    "github": {
        "owner": "pingcap",
        "repo": "tidb",
        "url": "https://github.com/pingcap/tidb"
    },
    "blog": {
        "url": "https://www.pingcap.com/blog/",
        "rss": "https://www.pingcap.com/blog/index.xml"
    },
    "website": "https://www.pingcap.com/tidb/",
    "keywords": ["tidb", "pingcap"]
    },

    "yugabytedb": {
    "name": "YugabyteDB",
    "category": "Distributed SQL",
    "github": {
        "owner": "yugabyte",
        "repo": "yugabyte-db",
        "url": "https://github.com/yugabyte/yugabyte-db"
    },
    "blog": {
        "url": "https://www.yugabyte.com/blog/",
        "rss": "https://www.yugabyte.com/feed/"
    },
    "website": "https://www.yugabyte.com",
    "keywords": ["yugabyte", "yugabytedb"]
    },

    "timescaledb": {
    "name": "TimescaleDB",
    "category": "Time Series",
    "github": {
        "owner": "timescale",
        "repo": "timescaledb",
        "url": "https://github.com/timescale/timescaledb"
    },
    "blog": {
        "url": "https://www.timescale.com/blog/",
        "rss": "https://www.timescale.com/blog/rss/"
    },
    "website": "https://www.timescale.com",
    "keywords": ["timescaledb", "timescale"]
    },

    "couchbase": {
    "name": "Couchbase",
    "category": "Document Store",
    "github": {
        "owner": "couchbase",
        "repo": "couchbase-server",
        "url": "https://github.com/couchbase/couchbase-server"
    },
    "blog": {
        "url": "https://blog.couchbase.com/",
        "rss": "https://blog.couchbase.com/feed/"
    },
    "website": "https://www.couchbase.com",
    "keywords": ["couchbase"]
    },

    "orientdb": {
    "name": "OrientDB",
    "category": "Multi-Model",
    "github": {
        "owner": "orientechnologies",
        "repo": "orientdb",
        "url": "https://github.com/orientechnologies/orientdb"
    },
    "blog": {
        "url": "https://orientdb.org/blog/",
        "rss": "https://orientdb.org/feed/"
    },
    "website": "https://orientdb.org",
    "keywords": ["orientdb"]
},


}


# ============================================
# CATÉGORIES DISPONIBLES
# ============================================

CATEGORIES = {
    "Key-Value": ["redis", "memcached"],
    "Document Store": ["mongodb", "couchdb"],
    "Graph": ["neo4j"],
    "Columnar": ["cassandra", "hbase"],
    "Distributed SQL": ["cockroachdb", "tidb", "yugabytedb"],
    "Search Engine": ["elasticsearch", "solr"],           
    "Time Series": ["influxdb", "timescaledb"],
    "Multi-Model": ["arangodb"], 
    "Relational SQL": ["postgresql", "mysql", "mariadb"]
}


# ============================================
# FONCTIONS UTILITAIRES
# ============================================

def get_database_config(db_key):
    """
    Récupérer la configuration complète d'une base de données.
    
    Args:
        db_key (str): Clé de la base de données (ex: "mongodb", "redis")
        
    Returns:
        dict: Configuration de la BDD ou None si non trouvée
        
    Exemple:
        >>> config = get_database_config("mongodb")
        >>> print(config['name'])
        'MongoDB'
        >>> print(config['category'])
        'Document Store'
    """
    # Convertir en minuscules pour être insensible à la casse
    db_key_lower = db_key.lower()
    
    # Récupérer la config
    config = DATABASES_CONFIG.get(db_key_lower)
    
    if config is None:
        print(f"Avertissement: Base de données '{db_key}' non trouvée dans la configuration")
        return None
    
    return config


def get_all_databases():
    """
    Récupérer la liste de toutes les bases de données configurées.
    
    Returns:
        list: Liste des clés de toutes les BDD
        
    Exemple:
        >>> databases = get_all_databases()
        >>> print(databases)
        ['mongodb', 'redis', 'neo4j', 'cockroachdb']
    """
    return list(DATABASES_CONFIG.keys())


def get_databases_by_category(category):
    """
    Récupérer toutes les bases de données d'une catégorie donnée.
    
    Args:
        category (str): Catégorie (ex: "Document Store", "Key-Value")
        
    Returns:
        list: Liste des clés des BDD de cette catégorie
        
    Exemple:
        >>> dbs = get_databases_by_category("Document Store")
        >>> print(dbs)
        ['mongodb']
    """
    # Liste pour stocker les résultats
    databases = []
    
    # Parcourir toutes les BDD
    for db_key, config in DATABASES_CONFIG.items():
        if config['category'] == category:
            databases.append(db_key)
    
    return databases


def get_all_categories():
    """
    Récupérer la liste de toutes les catégories disponibles.
    
    Returns:
        list: Liste des noms de catégories
        
    Exemple:
        >>> categories = get_all_categories()
        >>> print(categories)
        ['Key-Value', 'Document Store', 'Graph', 'Columnar', 'Distributed SQL']
    """
    return list(CATEGORIES.keys())


def validate_database(db_key):
    """
    Vérifier si une base de données existe dans la configuration.
    
    Args:
        db_key (str): Clé de la base de données
        
    Returns:
        bool: True si la BDD existe, False sinon
        
    Exemple:
        >>> validate_database("mongodb")
        True
        >>> validate_database("mysql")
        False
    """
    return db_key.lower() in DATABASES_CONFIG


def get_github_info(db_key):
    """
    Récupérer uniquement les informations GitHub d'une BDD.
    
    Args:
        db_key (str): Clé de la base de données
        
    Returns:
        dict: Informations GitHub (owner, repo, url) ou None
        
    Exemple:
        >>> info = get_github_info("mongodb")
        >>> print(f"{info['owner']}/{info['repo']}")
        'mongodb/mongo'
    """
    config = get_database_config(db_key)
    if config and 'github' in config:
        return config['github']
    return None


def get_rss_url(db_key):
    """
    Récupérer l'URL du flux RSS d'une BDD.
    
    Args:
        db_key (str): Clé de la base de données
        
    Returns:
        str: URL du flux RSS ou None
        
    Exemple:
        >>> url = get_rss_url("mongodb")
        >>> print(url)
        'https://www.mongodb.com/blog/rss.xml'
    """
    config = get_database_config(db_key)
    if config and 'blog' in config and 'rss' in config['blog']:
        return config['blog']['rss']
    return None


def get_keywords(db_key):
    """
    Récupérer les mots-clés de recherche CVE d'une BDD.
    
    Args:
        db_key (str): Clé de la base de données
        
    Returns:
        list: Liste des mots-clés ou []
        
    Exemple:
        >>> keywords = get_keywords("mongodb")
        >>> print(keywords)
        ['mongodb', 'mongo']
    """
    config = get_database_config(db_key)
    if config and 'keywords' in config:
        return config['keywords']
    return []


def print_database_info(db_key):
    """
    Afficher toutes les informations d'une base de données (pour debug).
    
    Args:
        db_key (str): Clé de la base de données
        
    Exemple:
        >>> print_database_info("mongodb")
        ╔════════════════════════════════════════╗
        ║  MongoDB (Document Store)              ║
        ╚════════════════════════════════════════╝
        Website: https://www.mongodb.com
        GitHub: mongodb/mongo
        RSS: https://www.mongodb.com/blog/rss.xml
        Keywords: mongodb, mongo
    """
    config = get_database_config(db_key)
    
    if not config:
        print(f"Base de données '{db_key}' non trouvée")
        return
    
    print(f"\n{'='*50}")
    print(f"  {config['name']} ({config['category']})")
    print(f"{'='*50}")
    print(f"Website: {config.get('website', 'N/A')}")
    
    if 'github' in config:
        github = config['github']
        print(f"GitHub: {github['owner']}/{github['repo']}")
    
    if 'blog' in config and 'rss' in config['blog']:
        print(f"RSS: {config['blog']['rss']}")
    
    if 'keywords' in config:
        keywords_str = ', '.join(config['keywords'])
        print(f"Keywords: {keywords_str}")
    
    print()


# ============================================
# tests
# ============================================

if __name__ == "__main__":
    """
    Tests rapides pour vérifier la configuration.
    Lance avec: python config/sources.py
    """
    
    print("Test de la configuration des sources\n")
    
    # Test 1: Lister toutes les BDD
    print("1️)Toutes les bases de données configurées:")
    all_dbs = get_all_databases()
    print(f"   {len(all_dbs)} BDD: {', '.join(all_dbs)}\n")
    
    # Test 2: Récupérer une config
    print("2️)Configuration de MongoDB:")
    print_database_info("mongodb")
    
    # Test 3: BDD par catégorie
    print("3️)Bases de données par catégorie:")
    for category in get_all_categories():
        dbs = get_databases_by_category(category)
        print(f"   {category}: {', '.join(dbs) if dbs else 'Aucune'}")
    print()
    
    # Test 4: Validation
    print("4️)Tests de validation:")
    print(f"   mongodb existe? {validate_database('mongodb')}")
    print(f"   mysql existe? {validate_database('mysql')}")
    print()
    
    # Test 5: Infos GitHub
    print("5️) Informations GitHub:")
    for db in all_dbs[:3]:  # Juste les 3 premières
        github = get_github_info(db)
        if github:
            print(f"   {db}: {github['owner']}/{github['repo']}")
    print()
    
    print("Yayy tous les tests passés!")