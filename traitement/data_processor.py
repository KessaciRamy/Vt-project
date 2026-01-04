"""
Module de traitement des données collectées.

Ce module nettoie, normalise, enrichit et valide les données
avant leur insertion dans PostgreSQL.
"""

import re
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import html


class DataProcessor:
    """
    Processeur principal pour transformer les données brutes
    en données propres et structurées.
    """
    
    def __init__(self, json_file: str):
        """
        Initialiser le processeur.
        
        Args:
            json_file: Chemin vers collected_data.json
        """
        self.json_file = json_file
        self.raw_data = []
        self.cleaned_data = []
        self.errors = []
        self.stats = {
            'total_items': 0,
            'processed': 0,
            'rejected': 0,
            'duplicates_removed': 0,
            'by_type': {}
        }
        
        print("\n" + "="*70)
        print("🔧 PROCESSEUR DE DONNÉES")
        print("="*70 + "\n")
    
    def load_data(self):
        """Charger les données depuis le fichier JSON"""
        print("📁 Chargement des données...")
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                self.raw_data = json.load(f)
            
            self.stats['total_items'] = len(self.raw_data)
            print(f"✅ {self.stats['total_items']} éléments chargés\n")
            return True
        
        except FileNotFoundError:
            print(f"❌ Fichier non trouvé: {self.json_file}")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Erreur de parsing JSON: {e}")
            return False
    
    def process_all(self):
        """
        Pipeline complet de traitement.
        
        Returns:
            List[Dict]: Données nettoyées et validées
        """
        if not self.load_data():
            return []
        
        print("🔄 Début du traitement...\n")
        
        # Traiter chaque élément
        for item in self.raw_data:
            try:
                processed_item = self._process_item(item)
                if processed_item:
                    self.cleaned_data.append(processed_item)
                    self.stats['processed'] += 1
                else:
                    self.stats['rejected'] += 1
            except Exception as e:
                self._log_error(item, str(e))
                self.stats['rejected'] += 1
        
        # Post-traitement
        print("\n🔍 Post-traitement...")
        self._remove_duplicates()
        self._update_statistics()
        
        # Afficher le résumé
        self._print_summary()
        
        return self.cleaned_data
    
    def _process_item(self, item: Dict) -> Optional[Dict]:
        """
        Traiter un élément individuel.
        
        Args:
            item: Données brutes d'un élément
        
        Returns:
            Dict nettoyé ou None si invalide
        """
        item_type = item.get('type')
        
        # 1. Validation de base
        if not self._validate_required_fields(item):
            return None
        
        # 2. Nettoyage
        cleaned = self._clean_item(item)
        
        # 3. Normalisation
        normalized = self._normalize_item(cleaned)
        
        # 4. Enrichissement selon le type
        if item_type == 'release':
            enriched = self._enrich_release(normalized)
        elif item_type == 'blog_post':
            enriched = self._enrich_blog_post(normalized)
        elif item_type == 'vulnerability':
            enriched = self._enrich_vulnerability(normalized)
        else:
            enriched = normalized
        
        # 5. Validation finale
        if self._validate_final(enriched):
            return enriched
        else:
            return None
    
    # ==========================================
    # NETTOYAGE
    # ==========================================
    
    def _clean_item(self, item: Dict) -> Dict:
        """Nettoyer un élément"""
        cleaned = item.copy()
        
        # Nettoyer le texte
        if 'title' in cleaned:
            cleaned['title'] = self._clean_text(cleaned['title'])
        
        if 'description' in cleaned:
            cleaned['description'] = self._clean_text(cleaned['description'], max_length=2000)
        
        # Nettoyer l'URL
        if 'url' in cleaned:
            cleaned['url'] = self._clean_url(cleaned['url'])
        
        return cleaned
    
    def _clean_text(self, text: str, max_length: int = None) -> str:
        """
        Nettoyer un texte.
        
        Args:
            text: Texte brut
            max_length: Longueur max (None = pas de limite)
        
        Returns:
            Texte nettoyé
        """
        if not text:
            return ""
        
        # Décoder les entités HTML
        text = html.unescape(text)
        
        # Supprimer les balises HTML résiduelles
        text = re.sub(r'<[^>]+>', '', text)
        
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text)
        
        # Supprimer les caractères de contrôle
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        # Nettoyer
        text = text.strip()
        
        # Tronquer si nécessaire
        if max_length and len(text) > max_length:
            text = text[:max_length-3] + "..."
        
        return text
    
    def _clean_url(self, url: str) -> str:
        """Nettoyer et valider une URL"""
        if not url:
            return ""
        
        url = url.strip()
        
        # Vérifier que c'est une URL valide
        if not url.startswith(('http://', 'https://')):
            return ""
        
        return url
    
    # ==========================================
    # NORMALISATION
    # ==========================================
    
    def _normalize_item(self, item: Dict) -> Dict:
        """Normaliser un élément"""
        normalized = item.copy()
        
        # Normaliser la date
        if 'date' in normalized:
            normalized['date'] = self._normalize_date(normalized['date'])
        
        # Normaliser les dates spécifiques aux CVE
        if 'published_date' in normalized:
            normalized['published_date'] = self._normalize_date(normalized['published_date'])
        
        if 'modified_date' in normalized:
            normalized['modified_date'] = self._normalize_date(normalized['modified_date'])
        
        return normalized
    
    def _normalize_date(self, date_str: str) -> str:
        """
        Normaliser une date au format YYYY-MM-DD.
        
        Args:
            date_str: Date en format quelconque
        
        Returns:
            Date normalisée YYYY-MM-DD
        """
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Si déjà au bon format
            datetime.strptime(date_str, '%Y-%m-%d')
            return date_str
        except:
            pass
        
        try:
            # Parser avec différents formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y']:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime('%Y-%m-%d')
                except:
                    continue
            
            # Dernière tentative avec dateutil
            from dateutil import parser
            dt = parser.parse(date_str)
            return dt.strftime('%Y-%m-%d')
        
        except:
            # Si échec, date actuelle
            return datetime.now().strftime('%Y-%m-%d')
    
    # ==========================================
    # ENRICHISSEMENT - RELEASES
    # ==========================================
    
    def _enrich_release(self, item: Dict) -> Dict:
        """Enrichir une release"""
        enriched = item.copy()
        
        # Parser la version
        version = enriched.get('version', '')
        version_info = self._parse_version(version)
        enriched.update(version_info)
        
        # Déterminer le type de release
        enriched['release_type'] = self._classify_release_type(
            version_info,
            enriched.get('description', ''),
            enriched.get('title', '')
        )
        
        # Extraire les features
        enriched['features'] = self._extract_features(enriched.get('description', ''))
        
        # Détecter breaking changes
        enriched['has_breaking_changes'] = self._detect_breaking_changes(
            enriched.get('description', '')
        )
        
        return enriched
    
    def _parse_version(self, version_str: str) -> Dict:
        """
        Parser un numéro de version (semantic versioning).
        
        Args:
            version_str: String de version (ex: "8.4.0", "8.4-RC1")
        
        Returns:
            Dict avec major, minor, patch, prerelease
        """
        # Nettoyer la version
        version = version_str.lower().strip()
        
        # Enlever les préfixes communs
        for prefix in ['v', 'r', 'release-', 'version-']:
            if version.startswith(prefix):
                version = version[len(prefix):]
        
        # Extraire pre-release info
        prerelease = None
        if '-' in version:
            version, prerelease = version.split('-', 1)
        
        # Parser les numéros
        parts = version.split('.')
        major = minor = patch = None
        
        try:
            if len(parts) >= 1:
                major = int(re.sub(r'\D', '', parts[0]))
            if len(parts) >= 2:
                minor = int(re.sub(r'\D', '', parts[1]))
            if len(parts) >= 3:
                patch = int(re.sub(r'\D', '', parts[2]))
        except:
            pass
        
        return {
            'version_major': major,
            'version_minor': minor,
            'version_patch': patch,
            'version_prerelease': prerelease,
            'version_clean': version
        }
    
    def _classify_release_type(self, version_info: Dict, description: str, title: str) -> str:
        """
        Classifier le type de release.
        
        Returns:
            'major', 'minor', 'patch', ou 'security'
        """
        # Vérifier si c'est un security patch
        security_keywords = ['security', 'cve', 'vulnerability', 'exploit', 'critical']
        text = (description + ' ' + title).lower()
        
        if any(kw in text for kw in security_keywords):
            return 'security'
        
        # Classifier selon semantic versioning
        major = version_info.get('version_major')
        minor = version_info.get('version_minor')
        patch = version_info.get('version_patch')
        
        # Si major change et minor/patch = 0, c'est une major release
        if major and minor == 0 and patch == 0:
            return 'major'
        
        # Si patch > 0, c'est un patch
        if patch and patch > 0:
            return 'patch'
        
        # Si minor > 0, c'est une minor release
        if minor and minor > 0:
            return 'minor'
        
        return 'unknown'
    
    def _extract_features(self, description: str) -> List[str]:
        """
        Extraire les features mentionnées dans la description.
        
        Returns:
            Liste des features trouvées
        """
        features = []
        
        # Patterns pour détecter les features
        patterns = [
            r'(?:New feature[s]?|Added|Introducing)[:\s]+([^\n]+)',
            r'[-*]\s+([A-Z][^:\n]+):',  # "- FEATURE_NAME: description"
            r'#\d+\s+([^:\n]+)',  # "- #14414 New command..."
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, description, re.IGNORECASE)
            for match in matches:
                feature = match.group(1).strip()
                if feature and len(feature) < 200:
                    features.append(feature)
        
        return features[:10]  # Max 10 features
    
    def _detect_breaking_changes(self, description: str) -> bool:
        """Détecter s'il y a des breaking changes"""
        breaking_keywords = [
            'breaking change',
            'backward incompatible',
            'migration required',
            'deprecat',
            'removed',
            'no longer supported'
        ]
        
        text = description.lower()
        return any(kw in text for kw in breaking_keywords)
    
    # ==========================================
    # ENRICHISSEMENT - BLOG POSTS
    # ==========================================
    
    def _enrich_blog_post(self, item: Dict) -> Dict:
        """Enrichir un article de blog"""
        enriched = item.copy()
        
        # Classifier la catégorie
        enriched['category'] = self._classify_blog_category(
            enriched.get('title', ''),
            enriched.get('description', ''),
            enriched.get('tags', [])
        )
        
        # Extraire les mots-clés techniques
        enriched['technical_keywords'] = self._extract_technical_keywords(
            enriched.get('title', '') + ' ' + enriched.get('description', '')
        )
        
        # Estimer le niveau technique
        enriched['technical_level'] = self._estimate_technical_level(
            enriched.get('description', '')
        )
        
        return enriched
    
    def _classify_blog_category(self, title: str, description: str, tags: List[str]) -> str:
        """
        Classifier la catégorie d'un article.
        
        Returns:
            'announcement', 'tutorial', 'performance', 'case_study', 'general'
        """
        text = (title + ' ' + description + ' ' + ' '.join(tags)).lower()
        
        # Patterns par catégorie
        categories = {
            'announcement': ['announcing', 'released', 'launch', 'introducing', 'new version'],
            'tutorial': ['how to', 'tutorial', 'guide', 'step by step', 'getting started'],
            'performance': ['performance', 'benchmark', 'speed', 'optimization', 'faster'],
            'case_study': ['case study', 'customer', 'success story', 'use case'],
        }
        
        for category, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return category
        
        return 'general'
    
    def _extract_technical_keywords(self, text: str) -> List[str]:
        """Extraire les mots-clés techniques importants"""
        # Liste de mots-clés techniques à rechercher
        technical_terms = [
            # Architecture
            'distributed', 'sharding', 'replication', 'clustering',
            'consistency', 'availability', 'partition tolerance',
            
            # Features
            'acid', 'transaction', 'vector search', 'full-text search',
            'graph', 'document', 'key-value', 'columnar',
            
            # Performance
            'indexing', 'caching', 'memory', 'throughput', 'latency',
            
            # Technologies
            'graphrag', 'rag', 'ai', 'machine learning', 'neural',
            'kubernetes', 'docker', 'cloud',
            
            # Security
            'encryption', 'authentication', 'authorization', 'ssl', 'tls'
        ]
        
        text_lower = text.lower()
        found_keywords = []
        
        for term in technical_terms:
            if term in text_lower:
                found_keywords.append(term)
        
        return found_keywords[:15]  # Max 15 keywords
    
    def _estimate_technical_level(self, text: str) -> str:
        """
        Estimer le niveau technique d'un article.
        
        Returns:
            'beginner', 'intermediate', 'advanced'
        """
        # Compter les termes techniques avancés
        advanced_terms = [
            'architecture', 'algorithm', 'implementation', 'protocol',
            'consensus', 'distributed', 'optimization', 'internals'
        ]
        
        text_lower = text.lower()
        advanced_count = sum(1 for term in advanced_terms if term in text_lower)
        
        if advanced_count >= 3:
            return 'advanced'
        elif advanced_count >= 1:
            return 'intermediate'
        else:
            return 'beginner'
    
    # ==========================================
    # ENRICHISSEMENT - VULNERABILITÉS
    # ==========================================
    
    def _enrich_vulnerability(self, item: Dict) -> Dict:
        """Enrichir une vulnérabilité"""
        enriched = item.copy()
        
        # Extraire CWE (type de vulnérabilité)
        enriched['cwe_id'] = self._extract_cwe(enriched.get('description', ''))
        
        # Extraire les versions affectées
        enriched['affected_versions'] = self._extract_affected_versions(
            enriched.get('description', '')
        )
        
        # Classifier par type d'impact
        enriched['impact_type'] = self._classify_cve_impact(
            enriched.get('description', '')
        )
        
        # Vérifier si un patch est disponible
        enriched['patch_available'] = self._check_patch_available(
            enriched.get('description', '')
        )
        
        return enriched
    
    def _extract_cwe(self, description: str) -> Optional[str]:
        """Extraire le CWE ID de la description"""
        match = re.search(r'CWE-(\d+)', description, re.IGNORECASE)
        if match:
            return f"CWE-{match.group(1)}"
        return None
    
    def _extract_affected_versions(self, description: str) -> str:
        """Extraire les versions affectées"""
        # Patterns courants
        patterns = [
            r'version[s]?\s+([\d\.]+(?:\s*(?:to|through|-)\s*[\d\.]+)?)',
            r'before\s+version\s+([\d\.]+)',
            r'([\d\.]+)\s+and\s+earlier'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "Unknown"
    
    def _classify_cve_impact(self, description: str) -> str:
        """
        Classifier le type d'impact d'une CVE.
        
        Returns:
            'rce', 'dos', 'info_disclosure', 'privilege_escalation', 'other'
        """
        text = description.lower()
        
        if any(kw in text for kw in ['remote code execution', 'rce', 'arbitrary code']):
            return 'rce'
        elif any(kw in text for kw in ['denial of service', 'dos', 'crash']):
            return 'dos'
        elif any(kw in text for kw in ['information disclosure', 'leak', 'expose']):
            return 'info_disclosure'
        elif any(kw in text for kw in ['privilege escalation', 'elevated privileges']):
            return 'privilege_escalation'
        else:
            return 'other'
    
    def _check_patch_available(self, description: str) -> bool:
        """Vérifier si un patch est mentionné"""
        text = description.lower()
        patch_keywords = ['patch', 'fixed in', 'update to', 'upgrade to', 'resolved in']
        return any(kw in text for kw in patch_keywords)
    
    # ==========================================
    # VALIDATION
    # ==========================================
    
    def _validate_required_fields(self, item: Dict) -> bool:
        """Valider les champs obligatoires selon le type"""
        item_type = item.get('type')
        
        required = {
            'release': ['database', 'title', 'date', 'version', 'url'],
            'blog_post': ['database', 'title', 'date', 'url'],
            'vulnerability': ['database', 'cve_id', 'severity', 'cvss_score', 'date']
        }
        
        if item_type not in required:
            self._log_error(item, f"Type inconnu: {item_type}")
            return False
        
        for field in required[item_type]:
            if field not in item or not item[field]:
                self._log_error(item, f"Champ obligatoire manquant: {field}")
                return False
        
        return True
    
    def _validate_final(self, item: Dict) -> bool:
        """Validation finale avant insertion"""
        # Vérifier l'URL
        if not item.get('url', '').startswith('http'):
            return False
        
        # Vérifier la date
        try:
            datetime.strptime(item['date'], '%Y-%m-%d')
        except:
            return False
        
        # Validations spécifiques aux CVE
        if item.get('type') == 'vulnerability':
            score = item.get('cvss_score', 0)
            if not (0.0 <= score <= 10.0):
                return False
        
        return True
    
    # ==========================================
    # POST-TRAITEMENT
    # ==========================================
    
    def _remove_duplicates(self):
        """Supprimer les doublons"""
        seen = set()
        unique_data = []
        
        for item in self.cleaned_data:
            # Créer une clé unique selon le type
            if item['type'] == 'vulnerability':
                key = item.get('cve_id')
            elif item['type'] == 'release':
                key = f"{item['database']}_{item.get('version')}"
            else:  # blog_post
                key = item.get('url')
            
            if key and key not in seen:
                seen.add(key)
                unique_data.append(item)
            else:
                self.stats['duplicates_removed'] += 1
        
        self.cleaned_data = unique_data
        print(f"🗑️  {self.stats['duplicates_removed']} doublons supprimés")
    
    def _update_statistics(self):
        """Mettre à jour les statistiques par type"""
        for item in self.cleaned_data:
            item_type = item.get('type', 'unknown')
            self.stats['by_type'][item_type] = self.stats['by_type'].get(item_type, 0) + 1
    
    # ==========================================
    # UTILITAIRES
    # ==========================================
    
    def _log_error(self, item: Dict, message: str):
        """Logger une erreur"""
        error = {
            'database': item.get('database', 'Unknown'),
            'type': item.get('type', 'Unknown'),
            'title': item.get('title', 'No title')[:50],
            'error': message
        }
        self.errors.append(error)
    
    def _print_summary(self):
        """Afficher le résumé du traitement"""
        print("\n" + "="*70)
        print("📊 RÉSUMÉ DU TRAITEMENT")
        print("="*70)
        print(f"   Total éléments    : {self.stats['total_items']}")
        print(f"   ✅ Traités         : {self.stats['processed']}")
        print(f"   ❌ Rejetés         : {self.stats['rejected']}")
        print(f"   🗑️  Doublons        : {self.stats['duplicates_removed']}")
        
        if self.stats['by_type']:
            print(f"\n   Par type:")
            for item_type, count in self.stats['by_type'].items():
                print(f"      {item_type:15s}: {count}")
        
        if self.errors:
            print(f"\n   ⚠️  Erreurs ({len(self.errors)}):")
            for error in self.errors[:5]:
                print(f"      - [{error['database']}] {error['error']}")
            if len(self.errors) > 5:
                print(f"      ... et {len(self.errors) - 5} autres")
        
        print("="*70 + "\n")
    
    def save_cleaned_data(self, output_file: str = 'cleaned_data.json'):
        """
        Sauvegarder les données nettoyées.
        
        Args:
            output_file: Nom du fichier de sortie
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.cleaned_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Données sauvegardées: {output_file}")
            print(f"   {len(self.cleaned_data)} éléments")
            return True
        
        except Exception as e:
            print(f"❌ Erreur de sauvegarde: {e}")
            return False

#pour faire marcher l api du traitement
def run_data_processing_api(
        input_file="collected_data.json",
        output_file="cleaned_data.json"
):
    processor = DataProcessor(input_file)
    cleaned_data = processor.process_all()

    if cleaned_data:
        processor.save_cleaned_data(output_file)

    return {
        "input_file": input_file,
        "output_file": output_file,
        "stats": processor.stats,
        "errors": processor.errors,
        "items_cleaned": len(cleaned_data)
    }
# ==========================================
# TESTS
# ==========================================

if __name__ == "__main__":
    """
    Test du processeur de données.
    Usage: python data_processor.py
    """
    
    print("\n" + "="*70)
    print("🧪 TEST DU PROCESSEUR DE DONNÉES")
    print("="*70 + "\n")
    
    # Créer le processeur
    processor = DataProcessor('collected_data.json')
    
    # Lancer le traitement
    cleaned_data = processor.process_all()
    
    if cleaned_data:
        # Sauvegarder
        processor.save_cleaned_data('cleaned_data.json')
        
        # Afficher quelques exemples
        print("\n📋 Exemples de données traitées:\n")
        
        for item_type in ['release', 'blog_post', 'vulnerability']:
            examples = [item for item in cleaned_data if item['type'] == item_type]
            if examples:
                print(f"   {item_type.upper()}:")
                example = examples[0]
                print(f"      Database: {example['database']}")
                print(f"      Title: {example['title'][:60]}...")
                if 'version_clean' in example:
                    print(f"      Version: {example['version_clean']}")
                if 'category' in example:
                    print(f"      Category: {example['category']}")
                if 'cvss_score' in example:
                    print(f"      CVSS: {example['cvss_score']}/10")
                print()
        
        print("✅ Traitement terminé avec succès!")
    else:
        print("❌ Aucune donnée traitée")