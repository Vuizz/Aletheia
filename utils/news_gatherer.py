import requests
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# Configuration
NEWSAPI_KEY = os.getenv("NEWS_API_KEY") # Get from newsapi.org
SAVE_PATH = "financial_news"
QUERIES = [
    "stocks OR stock market",
    "economy OR economic",
    "interest rates OR federal reserve",
    "earnings OR quarterly results",
    "cryptocurrency OR bitcoin"
]

def setup_directories():
    """Ensure save directory exists"""
    Path(SAVE_PATH).mkdir(exist_ok=True)

def fetch_news(query):
    """Fetch news from NewsAPI for a specific query"""
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 50,  # Max allowed for free tier
        "apiKey": NEWSAPI_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json().get("articles", [])
    except Exception as e:
        print(f"Error fetching news for '{query}': {str(e)}")
        return []

def process_articles(articles):
    """Clean and structure the article data"""
    processed = []
    for article in articles:
        processed.append({
            "source": article.get("source", {}).get("name"),
            "title": article.get("title"),
            "description": article.get("description"),
            "url": article.get("url"),
            "published_at": article.get("publishedAt"),
            "content": article.get("content")
        })
    return processed

def save_news(data):
    """Save news to JSON with date-based filename"""
    today = datetime.now().strftime("%Y-%m-%d")
    filename = Path(SAVE_PATH) / f"financial_news_{today}.json"
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(data)} articles to {filename}")
    except Exception as e:
        print(f"Error saving file: {str(e)}")

def main():
    setup_directories()
    all_articles = []
    
    print("Fetching financial news...")
    for query in QUERIES:
        articles = fetch_news(query)
        processed = process_articles(articles)
        all_articles.extend(processed)
        print(f"Found {len(processed)} articles for '{query}'")
        time.sleep(1)  # Respect API rate limits
    
    # Remove duplicates by URL
    unique_articles = {article["url"]: article for article in all_articles}.values()
    
    save_news(list(unique_articles))
    print("News collection complete!")

if __name__ == "__main__":
    import time  # Added for the sleep function
    main()