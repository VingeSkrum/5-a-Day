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


def run_news_pipeline():
    domains = {
        "BBC": "bbc.co.uk",
        "Sky News": "sky.com",
        "The Guardian": "theguardian.com"
    }

    print("\n📡 Fetching from allowed sources...")
    all_articles = []
    seen_titles = set()

    for name, domain in domains.items():
        articles = fetch_articles_from_source(domain)
        for article in articles:
            title = article.get("title")
            if title and title not in seen_titles:
                all_articles.append(article)
                seen_titles.add(title)

    print(f"\n✅ Fetched {len(all_articles)} articles total.")
    
    # Save full list to log
    with open("article_log.json", "w", encoding="utf-8") as f:
        json.dump(all_articles, f, indent=2)

    # 🧠 Rank and select top 5
    ranked_titles = rank_most_important_articles(all_articles, "general")
    final_selection = []
    for title in ranked_titles:
        for article in all_articles:
            if article["title"] == title:
                final_selection.append(article)
                break
        if len(final_selection) == 5:
            break

    # Save final 5
    with open("cached_articles.json", "w", encoding="utf-8") as f:
        json.dump(final_selection, f, indent=2)
    print(f"\n✅ Saved top {len(final_selection)} articles to cached_articles.json")



if __name__ == "__main__":
    run_news_pipeline()


