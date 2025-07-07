# Re-run the code to regenerate the new version of the news script after kernel reset
import requests
import json
import os
import time
from openai import OpenAI

# ---------------------
# ✅ CONFIGURATION
# ---------------------
print("🔐 OpenAI Key:", os.getenv("OPENAI_API_KEY")[:8], "..." if os.getenv("OPENAI_API_KEY") else "❌ Not Set")
API_KEY = os.getenv("GNEWS_API_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

LANG = "en"
COUNTRY = "gb"
ALLOWED_SOURCES = {"BBC", "Sky News", "The Guardian"}
MAX_REQUESTED = 20


# ---------------------
# 🤖 GPT Filters
# ---------------------
def gpt_select_top_5(articles):
    prompt = f"""You are a news editor. Here are 20 news articles. Choose the 5 most important and relevant stories for a general audience today. Ensure at least 1 story is about politics and 1 about sport if possible. Return ONLY the titles of the selected articles, one per line.

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
        print(f"❌ GPT selection failed: {e}")
        return []


# ---------------------
# 🌐 Fetch top headlines
# ---------------------
def fetch_top_articles():
    print("📡 Fetching 20 top GNews headlines...")
    params = {
        "token": API_KEY,
        "lang": LANG,
        "country": COUNTRY,
        "max": MAX_REQUESTED
    }

    try:
        response = requests.get("https://gnews.io/api/v4/top-headlines", params=params)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        print(f"✅ Retrieved {len(articles)} total articles")
        return [a for a in articles if a.get("source", {}).get("name") in ALLOWED_SOURCES]
    except Exception as e:
        print(f"❌ GNews request error: {e}")
        return []


# ---------------------
# 🚀 Run and Save
# ---------------------
def run_news_pipeline():
    articles = fetch_top_articles()
    if not articles:
        print("⚠️ No articles found.")
        return

    selected_titles = gpt_select_top_5(articles)
    final_articles = [a for a in articles if a["title"] in selected_titles]

    if len(final_articles) < 5:
        print(f"⚠️ Only selected {len(final_articles)} articles")

    with open("cached_articles.json", "w", encoding="utf-8") as f:
        json.dump(final_articles, f, indent=2)

    print(f"✅ Saved {len(final_articles)} articles to cached_articles.json")


# ---------------------
# ▶️ Main
# ---------------------
if __name__ == "__main__":
    run_news_pipeline()

