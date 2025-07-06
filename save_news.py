import requests
import json
import os
import time
from openai import OpenAI

# ---------------------
# ✅ CONFIGURATION
# ---------------------

API_KEY = os.environ.get("GNEWS_API_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CATEGORIES = ["world", "politics", "sport"]
LANG = "en"
COUNTRY = "gb"
ALLOWED_SOURCES = {"BBC", "Sky News", "The Guardian"}
MAX_REQUESTED = 15
MAX_FINAL = 2
MAX_ATTEMPTS_PER_CATEGORY = 2

# ---------------------
# 🔁 OpenAI Similarity Check
# ---------------------

def is_similar(article1, article2):
    prompt = f"""Are the following two news articles reporting the same story? Answer only 'Yes' or 'No'.

Article 1 Title: {article1["title"]}
Article 1 Description: {article1.get("description", "")}

Article 2 Title: {article2["title"]}
Article 2 Description: {article2.get("description", "")}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=5,
            temperature=0
        )
        answer = response.choices[0].message["content"].strip().lower()
        return "yes" in answer
    except Exception as e:
        print(f"❌ OpenAI similarity error: {e}")
        return False

# ---------------------
# 🧠 Relevance Check
# ---------------------

def is_relevant(article, category):
    prompt = f"""Is the following news article relevant to the topic category "{category}"? Answer only 'Yes' or 'No'.

Title: {article["title"]}
Description: {article.get("description", "")}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=5,
            temperature=0
        )
        answer = response.choices[0].message["content"].strip().lower()
        return "yes" in answer
    except Exception as e:
        print(f"❌ OpenAI relevance error: {e}")
        return False

# ---------------------
# 🔍 Fetch + Filter per Category
# ---------------------

def fetch_articles_for_category(category):
    unique_articles = []
    seen_titles = set()

    for attempt in range(1, MAX_ATTEMPTS_PER_CATEGORY + 1):
        print(f"🔁 Attempt {attempt} for '{category}'")

        params = {
            "token": API_KEY,
            "lang": LANG,
            "country": COUNTRY,
            "topic": category,
            "max": MAX_REQUESTED
        }

        try:
            response = requests.get("https://gnews.io/api/v4/top-headlines", params=params)
            response.raise_for_status()
            articles = response.json().get("articles", [])
            print(f"✅ Received {len(articles)} articles")

            # Filter by allowed sources
            filtered = [
                a for a in articles
                if a.get("source", {}).get("name") in ALLOWED_SOURCES
                and a.get("title") not in seen_titles
            ]

            print(f"✅ {len(filtered)} from allowed sources")

            for article in filtered:
                article["category"] = category
                seen_titles.add(article["title"])

                if not is_relevant(article, category):
                    print(f"⛔ Irrelevant: {article['title']}")
                    continue

                if any(is_similar(article, existing) for existing in unique_articles):
                    print(f"⛔ Duplicate: {article['title']}")
                    continue

                unique_articles.append(article)
                print(f"✅ Added: {article['title']}")

                if len(unique_articles) == MAX_FINAL:
                    break

                time.sleep(1.5)

        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed for '{category}': {e}")

        if len(unique_articles) >= 1:
            break

    return unique_articles

# ---------------------
# 🚀 Main Runner
# ---------------------

def run_news_pipeline():
    all_articles = []

    for category in CATEGORIES:
        print(f"\n📦 Category: {category}")
        category_articles = fetch_articles_for_category(category)

        if not category_articles:
            print(f"⚠️ No valid articles found for '{category}'")
        else:
            all_articles.extend(category_articles)

    # Save result
    if all_articles:
        with open("cached_articles.json", "w", encoding="utf-8") as f:
            json.dump(all_articles, f, indent=2)
        print(f"\n✅ Saved {len(all_articles)} articles to cached_articles.json")
    else:
        print("⚠️ No articles saved.")

# ---------------------
# ▶️ Entry Point
# ---------------------

if __name__ == "__main__":
    run_news_pipeline()


