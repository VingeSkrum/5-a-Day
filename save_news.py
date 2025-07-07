import requests
import json
import os
import time
from openai import OpenAI

# ---------------------
# 🔐 Setup
# ---------------------
print("\n🔐 Got OpenAI key:", os.getenv("OPENAI_API_KEY")[:8], "...")
API_KEY = os.environ.get("GNEWS_API_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

LANG = "en"
COUNTRY = "gb"
ALLOWED_DOMAINS = {
    "BBC": "bbc.co.uk",
    "Sky News": "sky.com",
    "The Guardian": "theguardian.com"
}

# ---------------------
# 🌐 Fetch articles from each domain
# ---------------------
def fetch_articles_from_source(domain):
    print(f"🌐 Fetching from {domain}...")
    params = {
        "token": API_KEY,
        "lang": LANG,
        "country": COUNTRY,
        "max": 10,
        "domain": domain
    }

    try:
        response = requests.get("https://gnews.io/api/v4/search", params=params)
        response.raise_for_status()
        return response.json().get("articles", [])
    except Exception as e:
        print(f"❌ Error fetching from {domain}: {e}")
        return []

# ---------------------
# 🧠 Rank most important articles using GPT
# ---------------------
def rank_most_important_articles(articles):
    prompt = f"""You are a trusted editor. Out of the following {len(articles)} news articles from major UK sources, select the 5 most important and relevant stories to include in a daily briefing. Return only the exact titles of those 5 stories, one per line.

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
        return [line.strip() for line in result.split("\n") if line.strip()]
    except Exception as e:
        print(f"❌ GPT ranking failed: {e}")
        return []

# ---------------------
# 🚀 Run pipeline
# ---------------------
def run_news_pipeline():
    all_articles = []
    seen_titles = set()

    print("\n📡 Fetching articles from allowed sources...")
    for name, domain in ALLOWED_DOMAINS.items():
        articles = fetch_articles_from_source(domain)
        for article in articles:
            title = article.get("title")
            if title and title not in seen_titles:
                all_articles.append(article)
                seen_titles.add(title)

    print(f"\n✅ Fetched {len(all_articles)} total unique articles.")

    # Save everything for debugging
    with open("article_log.json", "w", encoding="utf-8") as f:
        json.dump(all_articles, f, indent=2)
    print("🪵 Saved all articles to article_log.json")

    # Rank and select 5
    ranked_titles = rank_most_important_articles(all_articles)
    final_selection = []

    for title in ranked_titles:
        for article in all_articles:
            if article["title"] == title:
                final_selection.append(article)
                break
        if len(final_selection) == 5:
            break

    if not final_selection:
        print("⚠️ No final articles selected. Saving fallback.")
        final_selection = all_articles[:5]

    # Save final selection
    with open("cached_articles.json", "w", encoding="utf-8") as f:
        json.dump(final_selection, f, indent=2)

    print(f"\n✅ Saved {len(final_selection)} articles to cached_articles.json")

# ---------------------
# ▶️ Run
# ---------------------
if __name__ == "__main__":
    run_news_pipeline()


