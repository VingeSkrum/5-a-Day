# Updated script with world fallback to top-headlines and sport fallback to subtopics
import requests
import json
import os
import time
from openai import OpenAI

print("\n🔐 Got OpenAI key:", os.getenv("OPENAI_API_KEY")[:8], "...")
API_KEY = os.environ.get("GNEWS_API_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CATEGORIES = ["world", "politics", "sport"]
LANG = "en"
COUNTRY = "gb"
ALLOWED_SOURCES = {"BBC", "Sky News", "The Guardian"}
MAX_REQUESTED = 15
MAX_FINAL = 2
MAX_ATTEMPTS_PER_CATEGORY = 2
SPORT_SUBCATEGORIES = ["football", "tennis", "rugby", "cricket", "f1"]


def is_similar(article1, article2):
    prompt = f"""Are the following two news articles reporting the same story? Answer only 'Yes' or 'No'.\n\nArticle 1 Title: {article1["title"]}\nArticle 1 Description: {article1.get("description", "")}\n\nArticle 2 Title: {article2["title"]}\nArticle 2 Description: {article2.get("description", "")}\n"""
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


def is_relevant(article, category):
    prompt = f"""Is the following news article relevant to the topic category \"{category}\"? Answer only 'Yes' or 'No'.\n\nTitle: {article["title"]}\nDescription: {article.get("description", "")}\n"""
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


def rank_most_important_articles(articles, category):
    prompt = f"""You are a news editor. Here are {len(articles)} news articles in the category '{category}'. Choose the 2 that are the most important and relevant right now. Return only their titles, one per line.\n\n{json.dumps([{"title": a["title"], "description": a.get("description", "")} for a in articles], indent=2)}\n"""
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


def fetch_articles(topic, seen_titles):
    print(f"📡 Requesting GNews topic: {topic}")
    params = {
        "token": API_KEY,
        "lang": LANG,
        "country": COUNTRY,
        "topic": topic,
        "max": MAX_REQUESTED
    }
    try:
        response = requests.get("https://gnews.io/api/v4/top-headlines", params=params)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        return [
            a for a in articles
            if a.get("source", {}).get("name") in ALLOWED_SOURCES
            and a.get("title") not in seen_titles
        ]
    except Exception as e:
        print(f"❌ GNews fetch failed: {e}")
        return []


def fetch_articles_for_category(category, seen_titles):
    valid_articles = []

    for attempt in range(1, MAX_ATTEMPTS_PER_CATEGORY + 1):
        if category == "world":
            print("🌍 Using fallback: no 'world' topic, requesting general top headlines")
            params = {
                "token": API_KEY,
                "lang": LANG,
                "country": COUNTRY,
                "max": MAX_REQUESTED
            }
            response = requests.get("https://gnews.io/api/v4/top-headlines", params=params)
            try:
                articles = response.json().get("articles", [])
            except:
                articles = []
        elif category == "sport":
            print(f"⚽ Trying subcategories for 'sport': Attempt {attempt}")
            articles = []
            for sub in SPORT_SUBCATEGORIES:
                articles += fetch_articles(sub, seen_titles)
        else:
            articles = fetch_articles(category, seen_titles)

        print(f"✅ Fetched {len(articles)} articles for '{category}'")

        for article in articles:
            article["category"] = category
            if not is_relevant(article, category):
                continue
            valid_articles.append(article)
            time.sleep(1.5)

        if valid_articles:
            break

    selected_titles = rank_most_important_articles(valid_articles, category)
    selected = []

    for title in selected_titles:
        for article in valid_articles:
            if article["title"] == title and article["title"] not in seen_titles:
                seen_titles.add(article["title"])
                selected.append(article)
                break
        if len(selected) == MAX_FINAL:
            break

    return selected


def run_news_pipeline():
    all_articles = []
    seen_titles = set()

    for category in CATEGORIES:
        print(f"\n📦 Category: {category}")
        articles = fetch_articles_for_category(category, seen_titles)
        if articles:
            all_articles.extend(articles)

    with open("cached_articles.json", "w", encoding="utf-8") as f:
        json.dump(all_articles, f, indent=2)
    print(f"\n✅ Saved {len(all_articles)} articles.")


if __name__ == "__main__":
    run_news_pipeline()


