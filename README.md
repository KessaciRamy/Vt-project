# Module de Scraping - Veille NoSQL/NewSQL

Système de collecte automatique pour surveiller les releases, articles et vulnérabilités des bases de données NoSQL/NewSQL.

## Quick Start
```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. (Optionnel) Configurer les tokens
cp .env.example .env
# Éditer .env avec vos tokens

# 3. Lancer la collecte
python main_scraper.py
```

## Bases de données supportées

- MongoDB (Document Store)
- Redis (Key-Value)
- Neo4j (Graph)
- Cassandra (Columnar)
- Elasticsearch (Search Engine)
- InfluxDB (Time Series)
- CockroachDB (Distributed SQL)

## Résultat

Génère `collected_data.json` avec ~150+ éléments :
- Releases GitHub
- Articles de blog
- Vulnérabilités CVE
