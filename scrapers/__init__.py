"""
Package de scrapers pour la veille technologique.

Ce package contient tous les scrapers pour collecter des données
depuis différentes sources (GitHub, RSS, NVD).
"""

from .base_scraper import BaseScraper

__all__ = ['BaseScraper']