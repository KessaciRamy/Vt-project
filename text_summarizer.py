"""
Text Summarizer - Analyse et résumé automatique d'articles
VERSION AMÉLIORÉE : Stopwords bilingues + filtrage renforcé
"""

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from heapq import nlargest
from typing import List, Dict, Any
import re
import os
import json

# Télécharger les ressources NLTK (avec gestion d'erreurs)
def download_nltk_resources():
    """Télécharger les ressources NLTK nécessaires."""
    resources = [
        ('tokenizers/punkt', 'punkt'),
        ('corpora/stopwords', 'stopwords')
    ]
    
    for path, name in resources:
        try:
            nltk.data.find(path)
        except LookupError:
            try:
                print(f"📥 Téléchargement de {name}...")
                nltk.download(name, quiet=True)
                print(f"✅ {name} téléchargé")
            except Exception as e:
                print(f"⚠️  Erreur téléchargement {name}: {e}")

# Télécharger au démarrage
download_nltk_resources()


class ArticleSummarizer:
    """
    Classe pour générer des résumés automatiques des articles de blog.
    Supporte français, anglais, ou les deux langues.
    """
    
    def __init__(self, language='both'):
        """
        Initialiser le summarizer.
        
        Args:
            language: 'french', 'english' ou 'both' (défaut)
        """
        self.language = language
        
        # Charger les stopwords
        try:
            if language == 'french':
                self.stop_words = set(stopwords.words('french'))
            elif language == 'english':
                self.stop_words = set(stopwords.words('english'))
            else:  # 'both' - pour contenus multilingues
                french_stops = set(stopwords.words('french'))
                english_stops = set(stopwords.words('english'))
                self.stop_words = french_stops.union(english_stops)
                print(f"✅ Stopwords chargés: {len(self.stop_words)} mots (FR+EN)")
        except Exception as e:
            print(f"⚠️  Erreur chargement stopwords: {e}")
            self.stop_words = set()
        
        # Ajouter des mots custom supplémentaires
        self.stop_words.update([
            # Mots courts génériques
            'si', 'or', 'car', 'que', 'qui', 'quoi', 'où', 'dont',
            'the', 'and', 'for', 'from', 'with', 'will', 'can', 'has',
            'have', 'this', 'that', 'was', 'were', 'been', 'into',
            # Mots techniques génériques
            'new', 'more', 'all', 'any', 'some', 'out', 'use', 'using',
            'also', 'now', 'well', 'just', 'like', 'get', 'make', 'our',
            # Années (trop spécifiques)
            '2024', '2025', '2026'
        ])
    
    def summarize_article(self, text: str, num_sentences: int = 3) -> str:
        """Générer un résumé d'un article."""
        if not text or len(text.strip()) < 100:
            return text
        
        try:
            cleaned_text = self._preprocess_text(text)
            sentences = sent_tokenize(cleaned_text, language='french')
            
            if len(sentences) <= num_sentences:
                return " ".join(sentences)
            
            sentence_scores = self._score_sentences(sentences)
            summary_sentences = nlargest(num_sentences, sentence_scores, key=sentence_scores.get)
            summary_sentences = sorted(summary_sentences, key=lambda x: sentences.index(x))
            
            return " ".join(summary_sentences)
        except Exception as e:
            print(f"⚠️  Erreur summarize_article: {e}")
            return text[:500] + "..." if len(text) > 500 else text
    
    def _preprocess_text(self, text: str) -> str:
        """Nettoyer et pré-traiter le texte."""
        try:
            text = re.sub(r'http\S+|www\S+|https\S+', '', text)
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'[^\w\s.,!?-]', '', text)
            return text.strip()
        except Exception:
            return text
    
    def _score_sentences(self, sentences: List[str]) -> Dict[str, float]:
        """Calculer les scores des phrases avec NLTK."""
        try:
            all_words = word_tokenize(" ".join(sentences).lower())
            
            word_freq = {}
            for word in all_words:
                if word not in self.stop_words and word.isalnum() and len(word) > 2:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            if word_freq:
                max_freq = max(word_freq.values())
                for word in word_freq:
                    word_freq[word] = word_freq[word] / max_freq
            
            scores = {}
            for sentence in sentences:
                sentence_words = word_tokenize(sentence.lower())
                
                if len(sentence_words) < 5:
                    continue
                    
                score = 0
                for word in sentence_words:
                    if word in word_freq:
                        score += word_freq[word]
                
                if len(sentence_words) > 0:
                    score = score / len(sentence_words)
                scores[sentence] = score
            
            return scores
        except Exception as e:
            print(f"⚠️  Erreur _score_sentences: {e}")
            return {}
    
    def extract_keywords(self, text: str, num_keywords: int = 10) -> List[str]:
        """
        Extraire les mots-clés importants d'un texte.
        VERSION AMÉLIORÉE avec filtrage renforcé.
        """
        if not text:
            return []
        
        try:
            words = word_tokenize(text.lower())
            
            # Filtrer : stopwords, mots courts (< 4 lettres), chiffres
            filtered_words = [
                word for word in words 
                if (word not in self.stop_words and 
                    word.isalnum() and 
                    len(word) > 3 and  # Mots d'au moins 4 caractères
                    not word.isdigit())  # Pas de chiffres purs
            ]
            
            # Calculer les fréquences
            word_freq = {}
            for word in filtered_words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Filtrer les mots qui apparaissent trop peu (bruit)
            min_freq = 2 if len(filtered_words) > 50 else 1
            word_freq = {word: count for word, count in word_freq.items() 
                         if count >= min_freq}
            
            # Trier par fréquence
            sorted_words = sorted(word_freq.items(), 
                                key=lambda x: x[1], 
                                reverse=True)
            
            return [word[0] for word in sorted_words[:num_keywords]]
        except Exception as e:
            print(f"⚠️  Erreur extract_keywords: {e}")
            return []
    
    def analyze_blog_post(self, blog_post: Dict[str, Any]) -> Dict[str, Any]:
        """Analyser un article de blog complet."""
        try:
            title = blog_post.get('title', '')
            description = blog_post.get('description', '')
            
            full_text = f"{title}. {description}"
            
            summary = self.summarize_article(full_text)
            keywords = self.extract_keywords(full_text)
            word_count = len(word_tokenize(full_text)) if full_text else 0
            theme = self._categorize_theme(full_text)
            
            return {
                'original_title': title,
                'summary': summary,
                'keywords': keywords[:10],
                'word_count': word_count,
                'theme': theme,
                'read_time_minutes': max(1, word_count // 200)
            }
        except Exception as e:
            print(f"⚠️  Erreur analyze_blog_post: {e}")
            return {
                'original_title': blog_post.get('title', 'Erreur'),
                'summary': blog_post.get('description', '')[:200],
                'keywords': [],
                'word_count': 0,
                'theme': 'inconnu',
                'read_time_minutes': 1,
                'error': str(e)
            }
    
    def _categorize_theme(self, text: str) -> str:
        """Catégoriser l'article par thème (bilingue)."""
        try:
            text_lower = text.lower()
            
            themes = {
                'technique': [
                    # Français
                    'tutoriel', 'guide', 'déploiement', 'configuration', 'installation',
                    # Anglais
                    'tutorial', 'how to', 'deployment', 'setup', 'install'
                ],
                'sécurité': [
                    # Français
                    'sécurité', 'cve', 'vulnérabilité', 'patch', 'mise à jour',
                    # Anglais
                    'security', 'vulnerability', 'update', 'fix', 'patch'
                ],
                'performance': [
                    # Français
                    'performance', 'benchmark', 'optimisation', 'vitesse',
                    # Anglais
                    'performance', 'optimization', 'speed', 'faster', 'benchmark'
                ],
                'annonce': [
                    # Français
                    'annonce', 'nouveau', 'release', 'version', 'disponible',
                    # Anglais
                    'release', 'available', 'announcing', 'launched', 'new version'
                ],
                'cas pratique': [
                    # Français
                    "cas d'usage", 'exemple', 'étude de cas', 'implémentation',
                    # Anglais
                    'use case', 'example', 'case study', 'implementation'
                ]
            }
            
            for theme, keywords in themes.items():
                if any(keyword in text_lower for keyword in keywords):
                    return theme
            
            return 'général'
        except Exception:
            return 'inconnu'


# Singleton avec stopwords bilingues
summarizer = ArticleSummarizer(language='both')


def summarize_blog_posts(cleaned_data_file: str = 'cleaned_data.json') -> Dict[str, Any]:
    """Analyser et résumer tous les articles de blog."""
    try:
        if not os.path.isabs(cleaned_data_file):
            if not os.path.exists(cleaned_data_file):
                script_dir = os.path.dirname(os.path.abspath(__file__))
                cleaned_data_file = os.path.join(script_dir, cleaned_data_file)
        
        if not os.path.exists(cleaned_data_file):
            return {
                'total_posts': 0,
                'analyses': [],
                'error': f'Fichier {cleaned_data_file} introuvable'
            }
        
        with open(cleaned_data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        blog_posts = [item for item in data if item.get('type') == 'blog_post']
        
        if not blog_posts:
            return {
                'total_posts': 0,
                'analyses': [],
                'message': 'Aucun article de blog trouvé dans les données',
                'total_items': len(data)
            }
        
        analyses = []
        errors_count = 0
        
        for post in blog_posts:
            try:
                analysis = summarizer.analyze_blog_post(post)
                analysis['database'] = post.get('database', 'Inconnu')
                analysis['date'] = post.get('date', '')
                analysis['url'] = post.get('url', '')
                analyses.append(analysis)
            except Exception as e:
                errors_count += 1
                print(f"⚠️  Erreur sur un article : {e}")
                continue
        
        total_words = sum(a['word_count'] for a in analyses)
        themes_count = {}
        for analysis in analyses:
            theme = analysis['theme']
            themes_count[theme] = themes_count.get(theme, 0) + 1
        
        result = {
            'total_posts': len(blog_posts),
            'analyzed_posts': len(analyses),
            'errors_count': errors_count,
            'total_words': total_words,
            'avg_words_per_post': total_words // len(analyses) if analyses else 0,
            'themes_distribution': themes_count,
            'analyses': analyses,
            'message': f'Analysé {len(analyses)} articles sur {len(blog_posts)}'
        }
        
        return result
        
    except FileNotFoundError:
        return {
            'total_posts': 0,
            'analyses': [],
            'error': f'Fichier {cleaned_data_file} introuvable'
        }
    except json.JSONDecodeError:
        return {
            'total_posts': 0,
            'analyses': [],
            'error': f'Erreur de parsing JSON du fichier {cleaned_data_file}'
        }
    except Exception as e:
        return {
            'total_posts': 0,
            'analyses': [],
            'error': f'Erreur lors de l\'analyse: {str(e)}'
        }


# Test si exécuté directement
if __name__ == "__main__":
    print("🧪 Test du Text Summarizer (VERSION AMÉLIORÉE)")
    print("=" * 60)
    
    test_text = """
    PostgreSQL 17 introduces new features for improving database performance. 
    This version includes optimizations for vector search and better transaction 
    management. Developers can now use more efficient indexes for their queries.
    The new release also brings enhanced security features and backup capabilities.
    """
    
    print("\n1️⃣ Test de résumé :")
    summary = summarizer.summarize_article(test_text, num_sentences=2)
    print(f"   Résumé : {summary}")
    
    print("\n2️⃣ Test d'extraction de mots-clés :")
    keywords = summarizer.extract_keywords(test_text, num_keywords=10)
    print(f"   Mots-clés : {', '.join(keywords)}")
    print(f"   Nombre de mots-clés : {len(keywords)}")
    
    print("\n3️⃣ Test d'analyse complète :")
    test_post = {
        'title': 'PostgreSQL 17 - New Features',
        'description': test_text
    }
    analysis = summarizer.analyze_blog_post(test_post)
    print(f"   Thème : {analysis['theme']}")
    print(f"   Mots-clés extraits : {analysis['keywords']}")
    print(f"   Temps de lecture : {analysis['read_time_minutes']} min")
    
    print("\n✅ Tests terminés")