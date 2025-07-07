import requests
import json
import os
from openai import OpenAI

# ✅ CONFIG
print("\n🔐 Using OpenAI key:", os.getenv("OPENAI_API_KEY")[:8], "...")
GNEWS_API_KEY = os.environ.get("GNEWS_API_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

LANG = "en"
COUNTRY = "gb"
ALLOWED_SOURCES = {"BBC", "Sky News", "The Guardian"}
TOP_N = 20
FINAL_N = 5


def fetch_top_articles():
    print("📡 Fetching top headlines from GNews...")
    params = {
        "token": GNEWS_API_KEY,
        "lang": LANG,
        "country": COUNTRY,
        "max": TOP_N
    }

    try:
        response = requests.get("https://gnews.io/api/v4/top-headlines", params=params)
        response.raise_for_status()
        raw_articles = response.json().get("articles", [])

        articles = [
            a for a in raw_articles
            if a.get("source", {}).get("name") in ALLOWED_SOURCES
        ]

        print(f"✅ Got {len(articles)} articles from allowed sources.")

        # Save full log
        with open("article_log.json", "w", encoding="utf-8") as f:
            json.dump(articles, f, indent=2)
        print("📝 Saved full article log to article_log.json")

        return articles

    except Exception as e:
        print(f"❌ Failed to fetch top headlines: {e}")
        return []


def rank_articles_with_gpt(articles):
    prompt = f"""
You are a news editor. Rank the following articles from most to least important for a UK audience today. Choose the top {FINAL_N} most relevant, timely, and impactful stories across all topics (e.g., world, sport, politics, etc.).

Return EXACTLY {FINAL_N} article titles, one per line. Do not explain. Just output the titles.

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
        titles = [line.strip() for line in result.split("\n") if line.strip()]
        print(f"✅ GPT selected top {len(titles)} articles.")
        return titles
    except Exception as e:
        print(f"❌ GPT ranking error: {e}")
        return []


def run_pipeline():
    all_articles = fetch_top_articles()
    if not all_articles:
        print("⚠️ No articles to rank.")
        return

    ranked_titles = rank_articles_with_gpt(all_articles)
    selected = []

    seen = set()
    for title in ranked_titles:
        match = next((a for a in all_articles if a["title"] == title and a["title"] not in seen), None)
        if match:
            selected.append(match)
            seen.add(match["title"])
        if len(selected) == FINAL_N:
            break

    if len(selected) < FINAL_N:
        print(f"⚠️ Only found {len(selected)} matching GPT titles, padding with remaining top articles.")
        for a in all_articles:
            if a["title"] not in seen:
                selected.append(a)
                seen.add(a["title"])
            if len(selected) == FINAL_N:
                break

    with open("cached_articles.json", "w", encoding="utf-8") as f:
        json.dump(selected, f, indent=2)
    print(f"✅ Saved {len(selected)} final articles to cached_articles.json")


if __name__ == "__main__":
    run_pipeline()


