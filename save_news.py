# save_news.py

import requests
import json
from datetime import datetime

API_KEY = "32bf237815f80287e9186d538e0926fa"
BASE_URL = "https://gnews.io/api/v4/top-headlines"
CATEGORIES = ["world", "business", "technology", "sports"]
LANG = "en"
MAX_ARTICLES_PER_CATEGORY = 5

all_articles = []

for category in CATEGORIES:
    params = {
        "token": API_KEY,
        "lang": LANG,
        "topic": category,
        "max": MAX_ARTICLES_PER_CATEGORY
    }

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        for article in data.get("articles", []):
            article["category"] = category
            all_articles.append(article)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {category}: {e}")

with open("cached_articles.json", "w", encoding="utf-8") as f:
    json.dump(all_articles, f, indent=2)

print(f"✅ Saved {len(all_articles)} articles.")

