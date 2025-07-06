import requests
import json
import os
import time
from openai import OpenAI

# ---------------------
# ✅ CONFIGURATION
# ---------------------
print("✅ Got OpenAI key:", os.getenv("OPENAI_API_KEY")[:8], "...")
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
        answer = response.choices[0].message.content.strip().lower()
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
        answer = response.choices[0].message.content.strip().lower()
        return "yes" in answer
    except Exception as e:
        print(f"❌ OpenAI relevance error: {e}")
        return False

# ---------------------
# 🧠 GPT Ranks Most Important
# ---------------------

def rank_most_important_articles(articles, category):
    prompt = f"""You are a news editor. Here are {len(articles)} news articles in the category '{category}'. Choose the 2 that are the most important and relevant right now. Return only their titles, one per line.

{json.dumps([{"title": a["title"], "description": a.get("description", "")} for a in articles], indent=2)}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.3
        )
        result = response.choices[0].message.content.strip()
        selected_titles = [line.strip() for line in result.split("\n") if line.strip()]
        return selected_titles
    except Exception as e:
        print(f"❌ GPT ranking failed: {e}")
        return []

# ---------------------
# 🔍 Fetch + Filter per Category
# ---------------------
def fetch_articles_for_category(category, seen_titles):
    valid_articles = []

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

            # Filter by allowed sources and global duplicates
            filtered = [
                a for a in articles
                if a.get("source", {}).get("name") in ALLOWED_SOURCES
                and a.get("title") not in seen_titles
            ]

            print(f"✅ {len(filtered)} from allowed sources")

            for article in filtered:
                article["category"] = category

                if not is_relevant(article, category):
                    print(f"⛔ Irrelevant: {article['title']}")
                    continue

                valid_articles.append(article)

                time.sleep(1.5)

        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed for '{category}': {e}")

        if valid_articles:
            break

    # Ask GPT to pick top stories
    top_titles = rank_most_important_articles(valid_articles, category)
    selected = []

    for title in top_titles:
        for article in valid_articles:
            if article["title"] == title and article["title"] not in seen_titles:
                seen_titles.add(article["title"])
                selected.append(article)
                print(f"✅ Selected by GPT: {article['title']}")
                break

        if len(selected) == MAX_FINAL:
            break

    return selected

# ---------------------
# 🚀 Main Runner
# ---------------------
def run_news_pipeline():
    all_articles = []
    seen_titles = set()  # Track across all categories

    for category in CATEGORIES:
        print(f"\n📦 Category: {category}")
        category_articles = fetch_articles_for_category(category, seen_titles)

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


