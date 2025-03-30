import os
import json
import http.client
import logging
import asyncio
from typing import List, Dict, Optional
from urllib.parse import urlparse

import httpx
from newspaper import Article
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
SEARCH_NUM_RESULTS = 5
BLACKLIST_FILE = "blacklist.json"
FETCH_CONCURRENCY = 5  # Limit concurrent requests to avoid 429s

# -----------------------
# 🔍 Search (Serper API)
# -----------------------

logging.getLogger("httpx").setLevel(logging.WARNING)


def serper_search(query: str) -> List[Dict]:
    conn = http.client.HTTPSConnection("google.serper.dev")
    payload = json.dumps({"q": query})
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    conn.request("POST", "/news", payload, headers)
    res = conn.getresponse()
    data = res.read()
    decoded = json.loads(data.decode("utf-8"))
    return [{"title": item["title"], "link": item["link"]} for item in decoded.get("news", [])]

# -----------------------
# ⚠️ Domain Blacklist
# -----------------------


def load_blacklist() -> set:
    if not os.path.exists(BLACKLIST_FILE):
        return set()
    with open(BLACKLIST_FILE, "r") as f:
        return set(json.load(f))


def save_blacklist(domains: set):
    with open(BLACKLIST_FILE, "w") as f:
        json.dump(sorted(domains), f, indent=4)


def add_to_blacklist(domain: str):
    blacklist = load_blacklist()
    if domain not in blacklist:
        blacklist.add(domain)
        save_blacklist(blacklist)
        logging.info(f"Added {domain} to blacklist.")


def is_blacklisted(url: str) -> bool:
    domain = urlparse(url).netloc.replace("www.", "")
    return domain in load_blacklist()

# -----------------------
# 📰 Article Extraction
# -----------------------


async def fetch_and_parse_article(client: httpx.AsyncClient, url: str, title: str, semaphore: asyncio.Semaphore) -> Optional[Dict]:
    domain = urlparse(url).netloc.replace("www.", "")
    if is_blacklisted(url):
        logging.debug(f"Skipping blacklisted domain: {domain}")
        return None

    async with semaphore:
        try:
            response = await client.get(url, timeout=10)
            if response.status_code in (401, 403, 405, 406):
                add_to_blacklist(domain)
                return None
            if response.status_code == 302 and "/refresh?" in response.headers.get("location", ""):
                add_to_blacklist(domain)
                return None

            response.raise_for_status()

            def parse_article():
                article = Article(url)
                article.set_html(response.text)
                article.parse()
                article.nlp()
                return {
                    "title": title,
                    "url": url,
                    "text": article.summary
                }

            return await asyncio.to_thread(parse_article)

        except Exception as e:
            if any(code in str(e) for code in ["403", "401", "302", "405", "406"]):
                add_to_blacklist(domain)
            return None

# -----------------------
# 🔄 Query Handler
# -----------------------


async def get_articles_for_query_async(query: str, search_func=serper_search) -> List[Dict[str, str]]:
    try:
        search_results = search_func(query)
    except Exception as e:
        logging.warning(f"Search failed for query '{query}': {e}")
        return []

    articles = []
    semaphore = asyncio.Semaphore(FETCH_CONCURRENCY)

    async with httpx.AsyncClient() as client:
        tasks = [
            fetch_and_parse_article(
                client, item["link"], item["title"], semaphore)
            for item in search_results
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, dict):
            articles.append(result)

    return articles

# -----------------------
# 🧪 Test CLI
# -----------------------

if __name__ == "__main__":
    import time

    query = "latest news on Nvidia stock"
    start = time.time()
    articles = asyncio.run(get_articles_for_query_async(query))
    total_length = 0
    for article in articles:
        print(f"Title: {article['title']}")
        print(f"URL: {article['url']}")
        print(f"Text: {article['text'][:100]}...")
        print("-" * 80)
        total_length += len(article["text"])
    print(
        f"Fetched {len(articles)} articles, total text length: {total_length} characters")
    print(f"Time taken: {time.time() - start:.2f} seconds")
