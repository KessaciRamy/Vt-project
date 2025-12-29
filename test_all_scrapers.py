"""
Test complet de tous les scrapers.

Ce script teste le GitHub Scraper, RSS Scraper et NVD Scraper.
Lance avec: python test_all_scrapers.py
"""

print("\n" + "="*70)
print("🧪 TEST COMPLET DE TOUS LES SCRAPERS")
print("="*70 + "\n")

# ============================================
# TEST 1 : GitHub Scraper
# ============================================
print("="*70)
print("1️⃣ TEST DU GITHUB SCRAPER")
print("="*70 + "\n")

try:
    from scrapers.github_scraper import GitHubScraper
    
    # Créer le scraper
    github = GitHubScraper('mongodb')
    print(f"✅ GitHub Scraper créé: {github.name}")
    print(f"   Repository: {github.owner}/{github.repo}\n")
    
    # Récupérer les releases
    print("🔍 Récupération des 3 dernières releases...")
    releases = github.get_releases(limit=3)
    
    if releases:
        print(f"✅ {len(releases)} releases collectées\n")
        
        for i, release in enumerate(releases, 1):
            print(f"   {i}. {release['title']}")
            print(f"      Version: {release['version']}")
            print(f"      Date: {release['date']}")
            print(f"      URL: {release['url'][:50]}...")
            print()
    else:
        print("⚠️  Aucune release trouvée\n")
    
    # Vérifier le rate limit
    print("📊 Vérification du rate limit GitHub...")
    rate_info = github.check_rate_limit()
    if rate_info:
        print(f"   Limite: {rate_info['limit']} req/h")
        print(f"   Restant: {rate_info['remaining']}")
        
        if rate_info['remaining'] < 10:
            print(f"   ⚠️  Attention: Peu de requêtes restantes!")
    print()
    
    github_success = True
    print("✅ GitHub Scraper: OK\n")
    
except Exception as e:
    print(f"❌ ERREUR GitHub Scraper: {e}\n")
    import traceback
    traceback.print_exc()
    github_success = False

print()

# ============================================
# TEST 2 : RSS Scraper
# ============================================
print("="*70)
print("2️⃣ TEST DU RSS SCRAPER")
print("="*70 + "\n")

try:
    from scrapers.rss_scraper import RSSScraper
    
    # Créer le scraper
    rss = RSSScraper('mongodb')
    print(f"✅ RSS Scraper créé: {rss.name}")
    print(f"   URL RSS: {rss.rss_url}\n")
    
    # Informations du flux
    print("📰 Informations du flux RSS...")
    feed_info = rss.get_feed_info()
    if feed_info:
        print(f"   Titre: {feed_info['title']}")
        print(f"   Total d'articles: {feed_info['total_entries']}")
    print()
    
    # Récupérer les articles
    print("🔍 Récupération des 3 derniers articles...")
    posts = rss.get_blog_posts(limit=3)
    
    if posts:
        print(f"✅ {len(posts)} articles collectés\n")
        
        for i, post in enumerate(posts, 1):
            print(f"   {i}. {post['title']}")
            print(f"      Date: {post['date']}")
            print(f"      Auteur: {post.get('author', 'N/A')}")
            print(f"      URL: {post['url'][:50]}...")
            print()
    else:
        print("⚠️  Aucun article trouvé\n")
    
    rss_success = True
    print("✅ RSS Scraper: OK\n")
    
except Exception as e:
    print(f"❌ ERREUR RSS Scraper: {e}\n")
    import traceback
    traceback.print_exc()
    rss_success = False

print()

# ============================================
# TEST 3 : NVD Scraper
# ============================================
print("="*70)
print("3️⃣ TEST DU NVD SCRAPER")
print("="*70 + "\n")

try:
    from scrapers.nvd_scraper import NVDScraper
    
    # Créer le scraper
    nvd = NVDScraper('mongodb')
    print(f"✅ NVD Scraper créé: {nvd.name}")
    print(f"   Mots-clés: {', '.join(nvd.keywords)}")
    print(f"   Délai: {nvd.delay}s entre requêtes\n")
    
    # Récupérer les CVE
    print("🔍 Récupération de 3 CVE...")
    print("⏳ Cela peut prendre ~6 secondes (rate limit NVD)...\n")
    cves = nvd.get_vulnerabilities(limit=3)
    
    if cves:
        print(f"✅ {len(cves)} CVE collectés\n")
        
        # Compter les critiques
        critical_count = sum(1 for cve in cves if cve['is_critical'])
        if critical_count > 0:
            print(f"⚠️  {critical_count} CVE critiques/élevés!\n")
        
        for i, cve in enumerate(cves, 1):
            print(f"   {i}. {cve['cve_id']}")
            print(f"      Score: {cve['cvss_score']}/10 ({cve['severity']})")
            print(f"      Date: {cve['date']}")
            print(f"      Critique: {'OUI' if cve['is_critical'] else 'Non'}")
            print(f"      URL: {cve['url'][:50]}...")
            print()
    else:
        print("⚠️  Aucun CVE trouvé\n")
    
    nvd_success = True
    print("✅ NVD Scraper: OK\n")
    
except Exception as e:
    print(f"❌ ERREUR NVD Scraper: {e}\n")
    import traceback
    traceback.print_exc()
    nvd_success = False

print()

# ============================================
# RÉSUMÉ FINAL
# ============================================
print("="*70)
print("📊 RÉSUMÉ DES TESTS")
print("="*70 + "\n")

results = {
    'GitHub Scraper': github_success,
    'RSS Scraper': rss_success,
    'NVD Scraper': nvd_success
}

for scraper, success in results.items():
    status = "✅ OK" if success else "❌ ÉCHEC"
    print(f"   {scraper:20s} : {status}")

print()

all_success = all(results.values())

if all_success:
    print("="*70)
    print("🎉 TOUS LES SCRAPERS FONCTIONNENT PARFAITEMENT!")
    print("="*70)
    print("\n🎯 Prochaines étapes:")
    print("   1. Créer le Universal Collector")
    print("   2. Créer le script principal (main_scraper.py)")
    print("   3. Intégrer avec la base de données")
    print("\n💡 Tout est prêt pour continuer!\n")
else:
    print("="*70)
    print("⚠️  CERTAINS TESTS ONT ÉCHOUÉ")
    print("="*70)
    print("\n🔧 Vérifie:")
    print("   - Les dépendances sont installées (pip install -r requirements.txt)")
    print("   - Tu es connecté à Internet")
    print("   - Les URLs dans config/sources.py sont correctes")
    print("\n💡 Relance le test après correction.\n")

# Statistiques combinées
print("="*70)
print("📈 STATISTIQUES GLOBALES")
print("="*70 + "\n")

total_items = 0
if github_success and 'releases' in locals():
    total_items += len(releases)
if rss_success and 'posts' in locals():
    total_items += len(posts)
if nvd_success and 'cves' in locals():
    total_items += len(cves)

print(f"   Total d'éléments collectés: {total_items}")

if github_success:
    print(f"   - Releases: {len(releases)}")
if rss_success:
    print(f"   - Articles: {len(posts)}")
if nvd_success:
    print(f"   - CVE: {len(cves)}")
    if critical_count > 0:
        print(f"     (dont {critical_count} critiques)")

print("\n" + "="*70 + "\n")