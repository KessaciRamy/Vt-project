"""
Script de diagnostic pour GitHub API
"""

import os
from dotenv import load_dotenv
import requests

# Charger .env
load_dotenv()

token = os.getenv('GITHUB_TOKEN')

print("\n" + "="*60)
print("🔍 DIAGNOSTIC GITHUB API")
print("="*60 + "\n")

# Test 1: Vérifier le token
print("1️⃣ Vérification du token")
print("-" * 60)
if token:
    print(f"✅ Token trouvé: {token[:10]}...{token[-5:]}")
else:
    print("❌ Token non trouvé dans .env")
print()

# Test 2: Tester l'API GitHub directement
print("2️⃣ Test direct de l'API GitHub")
print("-" * 60)

url = "https://api.github.com/repos/mongodb/mongo/releases"
headers = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "Test-Script"
}

if token:
    headers["Authorization"] = f"Bearer {token}"

try:
    response = requests.get(url, headers=headers, timeout=10)
    
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Succès! Trouvé {len(data)} releases\n")
        
        if len(data) > 0:
            print("Premières releases:")
            for i, release in enumerate(data[:3], 1):
                print(f"   {i}. {release.get('tag_name', 'N/A')} - {release.get('name', 'N/A')}")
        else:
            print("⚠️  Aucune release dans la réponse")
    
    elif response.status_code == 404:
        print("❌ Repository non trouvé (404)")
    
    elif response.status_code == 403:
        print("❌ Rate limit dépassé ou token invalide (403)")
        print(f"Réponse: {response.text[:200]}")
    
    else:
        print(f"❌ Erreur: {response.status_code}")
        print(f"Réponse: {response.text[:200]}")

except Exception as e:
    print(f"❌ Exception: {e}")

print()

# Test 3: Vérifier le rate limit
print("3️⃣ Vérification du rate limit")
print("-" * 60)

try:
    rate_url = "https://api.github.com/rate_limit"
    response = requests.get(rate_url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        core = data['resources']['core']
        
        print(f"Limite: {core['limit']} req/h")
        print(f"Restant: {core['remaining']}")
        print(f"Reset à: {core['reset']}")
        
        if core['remaining'] < 10:
            print(f"\n⚠️  ATTENTION: Seulement {core['remaining']} requêtes restantes!")
    else:
        print(f"Impossible de vérifier: {response.status_code}")

except Exception as e:
    print(f"Erreur: {e}")

print()

# Test 4: Essayer avec une autre BDD
print("4️⃣ Test avec Redis")
print("-" * 60)

url2 = "https://api.github.com/repos/redis/redis/releases"

try:
    response2 = requests.get(url2, headers=headers, timeout=10)
    
    if response2.status_code == 200:
        data2 = response2.json()
        print(f"✅ Redis: {len(data2)} releases trouvées")
        if len(data2) > 0:
            print(f"   Dernière: {data2[0].get('tag_name', 'N/A')}")
    else:
        print(f"❌ Redis: Status {response2.status_code}")

except Exception as e:
    print(f"Erreur: {e}")

print()
print("="*60)
print("✅ DIAGNOSTIC TERMINÉ")
print("="*60 + "\n")