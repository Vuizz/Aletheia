import re
import os
from dotenv import load_dotenv
from newsapi import NewsApiClient
import json

load_dotenv()


import os
import json
from datetime import datetime

def fetch_top_headlines(date_filter=None, max_articles=None):
    """
    Fetch news headlines with optional date filtering.
    
    Args:
        date_filter (str or datetime): Date to filter articles. Can be:
            - None: return all articles
            - "today": return only today's articles
            - "YYYY-MM-DD" string: return articles from specific date
            - datetime object: return articles from specific date
        max_articles (int): Maximum number of articles to return (None for all)
    
    Returns:
        list: List of article dictionaries with title, description, and content
    """
    news_folder = "financial_news"
    news_files = os.listdir(news_folder)
    news_files = [f for f in news_files if f.endswith(".json")]
    
    # Sort files by name (assuming names contain dates) and take the most recent
    news_files.sort(reverse=True)
    
    all_articles = []
    
    for news_file in news_files:
        try:
            with open(f"{news_folder}/{news_file}", "r", encoding="utf8") as f:
                news = json.load(f)
                
            for article in news:
                # Parse article date (assuming it exists in the data)
                article_date = datetime.strptime(article["published_at"], "%Y-%m-%dT%H:%M:%SZ").date()
                
                # Apply date filter if specified
                if date_filter:
                    filter_date = None
                    if isinstance(date_filter, datetime):
                        filter_date = date_filter.date()
                    elif date_filter == "today":
                        filter_date = datetime.now().date()
                    else:
                        try:
                            filter_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
                        except ValueError:
                            raise ValueError("Invalid date_filter format. Use 'today', 'YYYY-MM-DD', or datetime object")
                    
                    if article_date != filter_date:
                        continue
                
                all_articles.append({
                    "title": article["title"],
                    "description": article["description"],
                    "content": article["content"] or "",
                    "date": article_date.isoformat()  # Include date in output
                })
                
                # Stop if we've reached max_articles
                if max_articles and len(all_articles) >= max_articles:
                    break
                    
            if max_articles and len(all_articles) >= max_articles:
                break
                
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error processing file {news_file}: {str(e)}")
            continue
    
    return all_articles[:max_articles] if max_articles else all_articles


def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def build_news_input_block(articles):
    return "\n\n".join(f"Headline: {a['title']}\nBody: {a['content'][:800]}..." for a in articles)


if __name__ == "__main__":
    articles = fetch_top_headlines()
    print(len(articles), "articles fetched")
    print(articles[0])