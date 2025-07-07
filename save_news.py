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
def rank_top_5_articles(articles):
    prompt = f"""You are a news editor selecting the five most important, relevant, and diverse news stories from this list. Try to include at least one related to politics and one to sport, if they exist. Return exactly 5 titles, one per line.

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
    print("\n📡 Fetching top 20 headlines...")
    params = {
        "token": API_KEY,
        "lang": LANG,
        "country": COUNTRY,
        "max": 20
    }

    try:
        response = requests.get("https://gnews.io/api/v4/top-headlines", params=params)
        response.raise_for_status()
        raw_articles = response.json().get("articles", [])

        # Filter by allowed sources
        articles = [
            a for a in raw_articles
            if a.get("source", {}).get("name") in ALLOWED_SOURCES
        ]

        print(f"✅ {len(articles)} valid articles from allowed sources.")

        selected_titles = rank_top_5_articles(articles)
        selected_articles = []

        for title in selected_titles:
            match = next((a for a in articles if a["title"] == title), None)
            if match:
                selected_articles.append(match)

        # Fallback: if GPT gives < 5, fill remaining
        if len(selected_articles) < 5:
            print(f"⚠️ Only {len(selected_articles)} selected by GPT. Filling with additional articles.")
            used_titles = {a["title"] for a in selected_articles}
            for a in articles:
                if a["title"] not in used_titles:
                    selected_articles.append(a)
                    used_titles.add(a["title"])
                if len(selected_articles) == 5:
                    break

        # Save
        with open("cached_articles.json", "w", encoding="utf-8") as f:
            json.dump(selected_articles, f, indent=2)
        print(f"\n✅ Saved {len(selected_articles)} articles to cached_articles.json")

    except Exception as e:
        print(f"❌ Fetch or save failed: {e}")



# ---------------------
# ▶️ Main
# ---------------------
if __name__ == "__main__":
    run_news_pipeline()

