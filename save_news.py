import requests
import json
import os
from openai import OpenAI

# ---------------------
# ✅ CONFIGURATION
# ---------------------
print("\n🔐 OpenAI key:", os.getenv("OPENAI_API_KEY")[:8], "...")
API_KEY = os.environ.get("GNEWS_API_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

LANG = "en"
COUNTRY = "gb"
ALLOWED_SOURCES = {"BBC", "Sky News", "The Guardian"}
MAX_FETCHED = 40
ARTICLES_TO_KEEP = 5

# ---------------------
# 🌐 Fetch from GNews
# ---------------------
def fetch_articles():
    print("🌍 Fetching top headlines...")
    params = {
        "token": API_KEY,
        "lang": LANG,
        "country": COUNTRY,
        "max": MAX_FETCHED
    }

    try:
        response = requests.get("https://gnews.io/api/v4/top-headlines", params=params)
        response.raise_for_status()
        return response.json().get("articles", [])
    except Exception as e:
        print(f"❌ GNews fetch error: {e}")
        return []

# ---------------------
# 🧠 Rank with OpenAI
# ---------------------
def rank_top_articles(articles):
    print("🤖 Ranking articles via OpenAI...")

    prompt = f"""You are a news editor. From the list of news stories below, choose the 5 most important and relevant to include in today's daily briefing. Return only the exact titles of the top 5, one per line.

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
# 🚀 Main Logic
# ---------------------
def run_news_pipeline():
    all_articles = fetch_articles()
    if not all_articles:
        print("⚠️ No articles fetched. Exiting.")
        return

    # Save log for review
    with open("article_log.json", "w", encoding="utf-8") as log:
        json.dump(all_articles, log, indent=2)
    print(f"🪵 Saved {len(all_articles)} raw articles to article_log.json")

    # First: Filter allowed sources
    allowed_articles = [a for a in all_articles if a.get("source", {}).get("name") in ALLOWED_SOURCES]
    print(f"✅ {len(allowed_articles)} articles from allowed sources")

    # If not enough, add articles from other sources
    if len(allowed_articles) < ARTICLES_TO_KEEP:
        print("➕ Supplementing with other sources")
        titles_included = {a["title"] for a in allowed_articles}
        for a in all_articles:
            if a["title"] not in titles_included:
                allowed_articles.append(a)
                titles_included.add(a["title"])
            if len(allowed_articles) >= ARTICLES_TO_KEEP * 2:  # feed GPT with more options
                break
        print(f"✅ Total pool after supplementing: {len(allowed_articles)}")

    # Rank with GPT
    selected_titles = rank_top_articles(allowed_articles)
    selected = []
    used_titles = set()

    for title in selected_titles:
        for article in allowed_articles:
            if article["title"] == title and article["title"] not in used_titles:
                selected.append(article)
                used_titles.add(article["title"])
                break
        if len(selected) == ARTICLES_TO_KEEP:
            break

    if len(selected) < ARTICLES_TO_KEEP:
        print(f"⚠️ GPT returned only {len(selected)}. Filling remaining manually.")
        for article in allowed_articles:
            if article["title"] not in used_titles:
                selected.append(article)
                used_titles.add(article["title"])
            if len(selected) == ARTICLES_TO_KEEP:
                break

    # Save final output
    with open("cached_articles.json", "w", encoding="utf-8") as f:
        json.dump(selected, f, indent=2)
    print(f"✅ Saved {len(selected)} final articles to cached_articles.json")


# ---------------------
# ▶️ ENTRY POINT
# ---------------------
if __name__ == "__main__":
    run_news_pipeline()
