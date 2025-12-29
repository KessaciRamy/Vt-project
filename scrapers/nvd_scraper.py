"""
NVD Scraper - Collecte les vulnérabilités (CVE) depuis l'API NVD

Ce scraper récupère les informations sur les vulnérabilités de sécurité
depuis la National Vulnerability Database (NVD).
"""

import sys
import os

# Fix PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from scrapers.base_scraper import BaseScraper
from config.sources import get_keywords

# Charger les variables d'environnement depuis .env
load_dotenv()


class NVDScraper(BaseScraper):
    """
    Scraper pour collecter les vulnérabilités (CVE) depuis NVD.
    
    Utilise l'API NVD (National Vulnerability Database) pour récupérer
    les failles de sécurité liées aux bases de données.
    """
    
    def __init__(self, db_key, api_key=None):
        """
        Initialiser le NVD Scraper.
        
        Args:
            db_key (str): Clé de la base de données (ex: "mongodb")
            api_key (str, optional): Clé API NVD pour augmenter le rate limit
        
        Exemple:
            >>> scraper = NVDScraper('mongodb')
            >>> scraper = NVDScraper('mongodb', api_key='your-key')
        """
        # Appeler le constructeur parent
        super().__init__(db_key)
        
        # Récupérer les mots-clés de recherche depuis la config
        self.keywords = get_keywords(db_key)
        
        if not self.keywords:
            raise ValueError(f"Pas de mots-clés CVE pour '{db_key}' dans la config")
        
        # Utiliser le premier mot-clé par défaut
        self.primary_keyword = self.keywords[0]
        
        # Clé API NVD (optionnelle)
        self.api_key = api_key
        if not self.api_key:
            # Essayer de récupérer depuis variable d'environnement
            self.api_key = os.getenv('NVD_API_KEY')
        
        # Définir le délai entre les requêtes selon la présence de la clé
        if self.api_key:
            self.delay = 0.6  # 50 requêtes / 30 secondes = 1 req toutes les 0.6s
            print(f"✅ [{self.name}] Clé API NVD configurée (50 req/30s)")
        else:
            self.delay = 6  # 5 requêtes / 30 secondes = 1 req toutes les 6s
            print(f"⚠️  [{self.name}] Pas de clé API NVD (5 req/30s)")
        
        # URL de base de l'API NVD
        self.api_base = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        
        print(f"🔍 [{self.name}] Mots-clés CVE: {', '.join(self.keywords)}")
    
    
    def get_vulnerabilities(self, limit=20):
        """
        Récupérer les vulnérabilités (CVE) depuis NVD.
        
        Args:
            limit (int): Nombre maximum de CVE à récupérer
        
        Returns:
            list: Liste de dictionnaires contenant les CVE
        
        Exemple:
            >>> scraper = NVDScraper('mongodb')
            >>> cves = scraper.get_vulnerabilities(limit=10)
            >>> print(f"Trouvé {len(cves)} CVE")
        """
        # Log
        print(f"🔍 [{self.name}] Collecte des CVE depuis NVD...")
        print(f"   Recherche: {self.primary_keyword}")
        
        # Construire les paramètres
        params = {
            'keywordSearch': self.primary_keyword,
            'resultsPerPage': min(limit, 2000)  # Max 2000 par requête
        }
        
        # Ajouter la clé API aux headers si présente
        headers = self.headers.copy()
        if self.api_key:
            headers['apiKey'] = self.api_key
        
        # Faire la requête
        response = self.make_request(
            self.api_base,
            params=params,
            headers=headers
        )
        
        if not response or response.status_code != 200:
            print(f"❌ [{self.name}] Échec de la collecte des CVE")
            return []
        
        # Parser la réponse JSON
        try:
            data = response.json()
            vulnerabilities = data.get('vulnerabilities', [])
        except Exception as e:
            print(f"❌ [{self.name}] Erreur de parsing JSON: {e}")
            return []
        
        # Traiter les CVE
        cves = []
        for vuln in vulnerabilities[:limit]:
            try:
                # Extraire les informations
                processed_cve = self._process_vulnerability(vuln)
                if processed_cve:
                    cves.append(processed_cve)
            except Exception as e:
                print(f"⚠️  [{self.name}] Erreur sur un CVE: {e}")
                continue
        
        print(f"✅ [{self.name}] {len(cves)} CVE collectés")
        
        # Compter les CVE critiques
        critical_count = sum(1 for cve in cves if cve.get('is_critical', False))
        if critical_count > 0:
            print(f"⚠️  [{self.name}] {critical_count} CVE critiques/élevés détectés!")
        
        # IMPORTANT: Respecter le rate limit
        print(f"⏳ [{self.name}] Attente de {self.delay}s (rate limit)...")
        time.sleep(self.delay)
        
        return cves
    
    
    def _process_vulnerability(self, vuln):
        """
        Traiter un CVE et extraire les infos importantes.
        
        Args:
            vuln (dict): Données brutes d'un CVE depuis l'API NVD
        
        Returns:
            dict: Données structurées du CVE
        """
        # Extraire les données du CVE
        cve = vuln.get('cve', {})
        
        # ID du CVE
        cve_id = cve.get('id', '')
        
        # Description
        descriptions = cve.get('descriptions', [])
        description = descriptions[0]['value'] if descriptions else "Pas de description"
        
        # Dates
        published = cve.get('published', '')
        modified = cve.get('lastModified', '')
        
        # Extraire le score CVSS (criticité)
        metrics = cve.get('metrics', {})
        cvss_score, severity = self._extract_cvss(metrics)
        
        # Déterminer si c'est critique
        is_critical = severity in ['CRITICAL', 'HIGH'] or cvss_score >= 7.0
        
        # Normaliser les dates
        pub_date = self._normalize_date(published)
        mod_date = self._normalize_date(modified)
        
        # Créer l'entrée avec le format uniforme
        entry = self.create_data_entry(
            source='nvd',
            data_type='vulnerability',
            title=cve_id,
            date=pub_date,
            description=description[:1000],  # Tronquer si trop long
            url=f"https://nvd.nist.gov/vuln/detail/{cve_id}",
            # Champs spécifiques aux CVE
            cve_id=cve_id,
            severity=severity,
            cvss_score=cvss_score,
            published_date=pub_date,
            modified_date=mod_date,
            is_critical=is_critical
        )
        
        return entry
    
    
    def _extract_cvss(self, metrics):
        """
        Extraire le score CVSS et la sévérité.
        
        Args:
            metrics (dict): Métriques du CVE
        
        Returns:
            tuple: (score, severity)
        """
        # Essayer CVSS v3.1 (le plus récent)
        if 'cvssMetricV31' in metrics and metrics['cvssMetricV31']:
            cvss_data = metrics['cvssMetricV31'][0]['cvssData']
            return (
                cvss_data.get('baseScore', 0.0),
                cvss_data.get('baseSeverity', 'UNKNOWN')
            )
        
        # Essayer CVSS v3.0
        if 'cvssMetricV30' in metrics and metrics['cvssMetricV30']:
            cvss_data = metrics['cvssMetricV30'][0]['cvssData']
            return (
                cvss_data.get('baseScore', 0.0),
                cvss_data.get('baseSeverity', 'UNKNOWN')
            )
        
        # Essayer CVSS v2.0 (ancien)
        if 'cvssMetricV2' in metrics and metrics['cvssMetricV2']:
            cvss_data = metrics['cvssMetricV2'][0]['cvssData']
            score = cvss_data.get('baseScore', 0.0)
            # v2 n'a pas de severity textuelle, on la calcule
            if score >= 7.0:
                severity = 'HIGH'
            elif score >= 4.0:
                severity = 'MEDIUM'
            else:
                severity = 'LOW'
            return (score, severity)
        
        # Pas de score disponible
        return (0.0, 'UNKNOWN')
    
    
    def _normalize_date(self, date_string):
        """
        Normaliser une date au format YYYY-MM-DD.
        
        Args:
            date_string (str): Date au format ISO
        
        Returns:
            str: Date normalisée
        """
        if not date_string:
            return datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Parser la date ISO
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
        except Exception:
            return datetime.now().strftime('%Y-%m-%d')
    
    
    def get_recent_vulnerabilities(self, days=30):
        """
        Récupérer les CVE des X derniers jours.
        
        Args:
            days (int): Nombre de jours en arrière
        
        Returns:
            list: Liste des CVE récents
        
        Exemple:
            >>> scraper = NVDScraper('mongodb')
            >>> recent = scraper.get_recent_vulnerabilities(days=30)
            >>> print(f"{len(recent)} CVE dans les 30 derniers jours")
        """
        # Calculer les dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Formater pour l'API (ISO 8601)
        pub_start = start_date.strftime("%Y-%m-%dT00:00:00.000")
        pub_end = end_date.strftime("%Y-%m-%dT23:59:59.999")
        
        print(f"🔍 [{self.name}] Recherche CVE entre {start_date.date()} et {end_date.date()}")
        
        # Construire les paramètres
        params = {
            'keywordSearch': self.primary_keyword,
            'pubStartDate': pub_start,
            'pubEndDate': pub_end,
            'resultsPerPage': 100
        }
        
        # Ajouter la clé API si présente
        headers = self.headers.copy()
        if self.api_key:
            headers['apiKey'] = self.api_key
        
        # Faire la requête
        response = self.make_request(
            self.api_base,
            params=params,
            headers=headers
        )
        
        if not response or response.status_code != 200:
            return []
        
        try:
            data = response.json()
            total = data.get('totalResults', 0)
            print(f"📊 [{self.name}] {total} CVE trouvés dans les {days} derniers jours")
            
            vulnerabilities = data.get('vulnerabilities', [])
            
            # Traiter les CVE
            cves = []
            for vuln in vulnerabilities:
                processed = self._process_vulnerability(vuln)
                if processed:
                    cves.append(processed)
            
            # Rate limit
            time.sleep(self.delay)
            
            return cves
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return []
    
    
    def get_critical_vulnerabilities(self, limit=20):
        """
        Récupérer uniquement les CVE critiques/élevés.
        
        Args:
            limit (int): Nombre maximum de CVE
        
        Returns:
            list: Liste des CVE critiques
        
        Exemple:
            >>> scraper = NVDScraper('mongodb')
            >>> critical = scraper.get_critical_vulnerabilities()
            >>> print(f"{len(critical)} CVE critiques")
        """
        # Récupérer tous les CVE
        all_cves = self.get_vulnerabilities(limit=limit)
        
        # Filtrer les critiques
        critical = [cve for cve in all_cves if cve.get('is_critical', False)]
        
        print(f"⚠️  [{self.name}] {len(critical)} CVE critiques sur {len(all_cves)} total")
        
        return critical


# ============================================
# TESTS
# ============================================

if __name__ == "__main__":
    """
    Tests du NVD Scraper.
    Lance avec: python -m scrapers.nvd_scraper
    """
    
    print("\n" + "="*60)
    print("🧪 TEST DU NVD SCRAPER")
    print("="*60 + "\n")
    
    # Test 1: Initialisation
    print("1️⃣ Test d'initialisation")
    print("-" * 60)
    try:
        scraper = NVDScraper('mongodb')
        print(f"✅ NVD Scraper créé pour {scraper.name}")
        print(f"   Mots-clés: {', '.join(scraper.keywords)}")
        print(f"   Délai entre requêtes: {scraper.delay}s")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        exit(1)
    print()
    
    # Test 2: Récupération des CVE
    print("2️⃣ Test de récupération des CVE")
    print("-" * 60)
    print("⏳ Cette requête peut prendre ~6 secondes (rate limit)...")
    try:
        cves = scraper.get_vulnerabilities(limit=5)
        
        if cves:
            print(f"✅ {len(cves)} CVE récupérés\n")
            
            # Afficher les détails du premier CVE
            first = cves[0]
            print("   Premier CVE:")
            print(f"   🆔 ID: {first['cve_id']}")
            print(f"   📊 Score: {first['cvss_score']}/10")
            print(f"   ⚠️  Sévérité: {first['severity']}")
            print(f"   📅 Date: {first['date']}")
            print(f"   🔗 URL: {first['url']}")
            print(f"   🚨 Critique: {'OUI' if first['is_critical'] else 'Non'}")
            print(f"   📄 Description: {first['description'][:100]}...")
        else:
            print("⚠️  Aucun CVE trouvé")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    print()
    
    # Test 3: CVE récents (30 derniers jours)
    print("3️⃣ Test des CVE récents (30 derniers jours)")
    print("-" * 60)
    print("⏳ Cette requête peut prendre ~6 secondes (rate limit)...")
    try:
        recent = scraper.get_recent_vulnerabilities(days=30)
        
        if recent:
            print(f"✅ {len(recent)} CVE trouvés dans les 30 derniers jours")
            
            # Compter les critiques
            critical_count = sum(1 for cve in recent if cve['is_critical'])
            print(f"   ⚠️  Dont {critical_count} critiques/élevés")
        else:
            print("ℹ️  Aucun CVE récent trouvé")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    print()
    
    # Test 4: CVE critiques uniquement
    print("4️⃣ Test des CVE critiques uniquement")
    print("-" * 60)
    print("⏳ Cette requête peut prendre ~6 secondes (rate limit)...")
    try:
        critical = scraper.get_critical_vulnerabilities(limit=10)
        
        if critical:
            print(f"⚠️  {len(critical)} CVE critiques trouvés\n")
            
            # Afficher le top 3
            print("   Top 3 des plus critiques:")
            sorted_cves = sorted(critical, key=lambda x: x['cvss_score'], reverse=True)
            for i, cve in enumerate(sorted_cves[:3], 1):
                print(f"   {i}. {cve['cve_id']} - Score: {cve['cvss_score']}/10 ({cve['severity']})")
        else:
            print("✅ Aucun CVE critique récent (bonne nouvelle!)")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    print()
    
    # Test 5: Statistiques
    print("5️⃣ Statistiques")
    print("-" * 60)
    stats = scraper.get_statistics()
    print(f"   Total requêtes: {stats['total_requests']}")
    print(f"   Succès: {stats['successful']}")
    print(f"   Erreurs: {stats['errors']}")
    print(f"   Taux de succès: {stats['success_rate']}%")
    print()
    
    print("="*60)
    print("✅ TESTS NVD SCRAPER TERMINÉS")
    print("="*60)
    print("\n💡 Note: Le NVD est lent (rate limit). C'est normal.")
    print("💡 Pour aller plus vite, obtiens une clé API NVD.\n")