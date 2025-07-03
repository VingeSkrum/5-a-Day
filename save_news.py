import requests
import json
import os

API_KEY = "32bf237815f80287e9186d538e0926fa"  # Or hardcode your key
BASE_URL = "https://gnews.io/api/v4/top-headlines"
CATEGORIES = ["sport", "world", "business", "technology"]
LANG = "en"
MAX_ARTICLES = 1  # Only one per category

articles = []

for category in CATEGORIES:
    print(f"Fetching {category}...")  # 👈 debug log

    params = {
        "token": API_KEY,
        "lang": LANG,
        "topic": category,
        "max": MAX_ARTICLES
    }

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("articles"):
            top_article = data["articles"][0]
            top_article["category"] = category
            articles.append(top_article)
            print(f"✅ Found article for '{category}': {top_article['title']}")
        else:
            print(f"⚠️ No articles for category '{category}'")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching {category}: {e}")

with open("cached_articles.json", "w", encoding="utf-8") as f:
    json.dump(articles, f, indent=2)

print(f"✅ Saved {len(articles)} articles.")


