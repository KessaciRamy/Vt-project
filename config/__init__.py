"""
Package de configuration pour le module de scraping.
"""

from .sources import (
    DATABASES_CONFIG,
    CATEGORIES,
    get_database_config,
    get_all_databases,
    get_databases_by_category,
    get_all_categories,
    validate_database,
    get_github_info,
    get_rss_url,
    get_keywords
)

__all__ = [
    'DATABASES_CONFIG',
    'CATEGORIES',
    'get_database_config',
    'get_all_databases',
    'get_databases_by_category',
    'get_all_categories',
    'validate_database',
    'get_github_info',
    'get_rss_url',
    'get_keywords'
]