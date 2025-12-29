# Module de Scraping - Veille Technologique NoSQL/NewSQL

Système de collecte automatique pour surveiller les releases, articles de blog et vulnérabilités (CVE) des bases de données NoSQL et NewSQL.

## Objectif

Collecter automatiquement des informations sur 7 bases de données depuis 3 sources :
- **GitHub** : Nouvelles releases/versions
- **RSS** : Articles de blog officiels
- **NVD** : Vulnérabilités (CVE)

**Performance :** ~10 secondes avec tokens API (gratuits) ou ~40 secondes sans tokens.

## Résultat

Génère un fichier `collected_data.json` contenant ~150-180 éléments structurés, prêts pour intégration PostgreSQL.

## Quick Start

```bash
# 1. Cloner le repository
git clone https://github.com/[username]/DB-Scraper.git
cd DB-Scraper

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. (Optionnel mais recommandé) Configurer les tokens API
# Les tokens rendent la collecte 4x plus rapide (40s → 10s)
# Guide complet: voir section "Configuration des API Keys" ci-dessous
# Éditer .env avec vos tokens 

# 4. Lancer la collecte
python main_scraper.py
```

**Résultat :** Fichier `collected_data.json` généré en ~10 secondes (avec tokens) ou ~40 secondes (sans tokens).

## Configuration des API Keys (Optionnel mais Recommandé)

### Pourquoi configurer les tokens ?

Les tokens API sont **optionnels** mais **fortement recommandés** pour de meilleures performances :

### Comment obtenir les tokens ?

#### Token GitHub 

1. Allez sur https://github.com/settings/tokens
2. Cliquez sur "Generate new token (classic)"
3. **Cochez SEULEMENT** `public_repo`
4. Générez et copiez le token (`ghp_xxxxx`)

#### Clé API NVD (attente email)

1. Allez sur https://nvd.nist.gov/developers/request-an-api-key
2. Remplissez le formulaire (email, organisation, nom)
3. Vous recevrez la clé par email (quelques heures max)

#### Configuration

```bash
# Créer le fichier .env
# Éditer .env et ajouter vos tokens
GITHUB_TOKEN=ghp_votre_token_ici
NVD_API_KEY=votre_clé_ici
```

**Important :** Chaque personne crée SON PROPRE `.env` avec SES tokens. Ne partagez jamais votre fichier `.env` !

## Bases de données supportées

| Base de données | Catégorie | Releases | Articles | CVE |
|-----------------|-----------|----------|----------|-----|
| MongoDB | Document Store | ⚠️ | ⚠️ | ✅ |
| Redis | Key-Value | ✅ | ⚠️ | ✅ |
| Neo4j | Graph | ✅ | ✅ | ✅ |
| Cassandra | Columnar | ⚠️ | ⚠️ | ✅ |
| Elasticsearch | Search Engine | ✅ | ✅ | ✅ |
| InfluxDB | Time Series | ✅ | ⚠️ | ✅ |
| CockroachDB | Distributed SQL | ⚠️ | ⚠️ | ⚠️ |

⚠️ = Source non disponible (flux RSS mal formé, pas de releases GitHub publiques, ou aucune vulnérabilité connue)

## Utilisation

### Collecter toutes les bases de données

```bash
python main_scraper.py
```

### Collecter des bases spécifiques

```bash
# Une seule base de données
python main_scraper.py --db redis

# Plusieurs bases de données
python main_scraper.py --db redis neo4j elasticsearch

# Personnaliser les limites
python main_scraper.py --releases 20 --posts 20 --cves 50
```

### Fichier de sortie personnalisé

```bash
python main_scraper.py --output mes_donnees.json
```

### Aide

```bash
python main_scraper.py --help
```

## Format des données

Le fichier `collected_data.json` contient une liste d'objets structurés :

```json
[
  {
    "source": "github",
    "database": "Redis",
    "category": "Key-Value",
    "type": "release",
    "title": "Redis 8.4.0",
    "date": "2024-12-15",
    "url": "https://github.com/redis/redis/releases/tag/8.4.0",
    "version": "8.4.0",
    ...
  },
  {
    "source": "nvd",
    "database": "MongoDB",
    "type": "vulnerability",
    "cve_id": "CVE-2024-1234",
    "severity": "HIGH",
    "cvss_score": 8.2,
    "is_critical": true,
    ...
  }
]
```

**3 types de données :**
- `release` : Versions/releases GitHub
- `blog_post` : Articles de blog
- `vulnerability` : CVE (vulnérabilités)

## Architecture

```
DB-Scraper/
├── config/
│   └── sources.py          # Configuration des 7 BDD
├── scrapers/
│   ├── base_scraper.py     # Classe de base (gestion erreurs, retry)
│   ├── github_scraper.py   # Collecte releases GitHub
│   ├── rss_scraper.py      # Collecte articles blog (RSS)
│   ├── nvd_scraper.py      # Collecte CVE (NVD)
│   └── universal_collector.py  # Combine les 3 scrapers
├── main_scraper.py         # Script principal
├── requirements.txt        # Dépendances Python
└── .env.example           # Template pour tokens
```

## Dépendances

- Python 3.8+
- requests
- beautifulsoup4
- feedparser
- python-dateutil
- python-dotenv

Installation : `pip install -r requirements.txt`

## Ajouter une nouvelle base de données

1. Éditer `config/sources.py`
2. Ajouter la configuration de la BDD
3. Lancer : `python main_scraper.py --db votre_nouvelle_bdd`

## Intégration PostgreSQL

Le fichier `collected_data.json` est prêt pour être inséré dans PostgreSQL.

## Tests

```bash
# Tester la configuration
python config/sources.py

# Tester un scraper individuel
python -m scrapers.github_scraper
python -m scrapers.rss_scraper
python -m scrapers.nvd_scraper

# Test rapide avec Redis
python test_redis_quick.py

# Test complet
python test_all_scrapers.py
```

## Statistiques

**Dernière collecte (7 BDD) :**
- 159 éléments collectés
- 40 releases GitHub
- 20 articles de blog
- 99 CVE (dont 58 critiques ⚠️)
- Fichier : 138 KB
- Temps : ~10 secondes (avec tokens)
