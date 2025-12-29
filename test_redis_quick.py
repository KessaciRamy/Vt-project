"""
Test rapide avec Redis pour vérifier que tout fonctionne.
"""

from scrapers.universal_collector import UniversalCollector

print("\n" + "="*70)
print("🧪 TEST RAPIDE AVEC REDIS")
print("="*70 + "\n")

# Créer le collector
collector = UniversalCollector('redis')

# Collecter toutes les données
all_data = collector.collect_all(
    releases_limit=5,
    posts_limit=5,
    cves_limit=5
)

# Statistiques
stats = collector.get_statistics()

print("\n" + "="*70)
print("✅ TEST TERMINÉ")
print("="*70)
print(f"\nRésultat: {stats['total']} éléments collectés")
print(f"   - {stats['releases']} releases")
print(f"   - {stats['blog_posts']} articles")
print(f"   - {stats['vulnerabilities']} CVE")

if stats['critical_cves'] > 0:
    print(f"   ⚠️  {stats['critical_cves']} CVE critiques!")

print("\n💾 Pour sauvegarder les données:")
print("   import json")
print("   with open('redis_data.json', 'w') as f:")
print("       json.dump(all_data, f, indent=2)")
print()