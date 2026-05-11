"""
Scout Module
Keyword-based research across web, Reddit, LinkedIn, news, reviews, and X.
Uses Serper.dev API.
"""
import requests
import logging

logger = logging.getLogger(__name__)

SERPER_SEARCH_URL = "https://google.serper.dev/search"
SERPER_NEWS_URL   = "https://google.serper.dev/news"


def _serper_search(query: str, api_key: str, num: int = 10, endpoint: str = SERPER_SEARCH_URL) -> dict:
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    try:
        r = requests.post(endpoint, json={"q": query, "num": num}, headers=headers, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"Serper request failed for '{query}': {e}")
        return {}


def _parse_organic(results: dict, source: str = "web") -> list[dict]:
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("link", ""),
            "snippet": r.get("snippet", ""),
            "source": source,
        }
        for r in results.get("organic", [])
        if r.get("title") or r.get("snippet")
    ]


def _parse_news(results: dict) -> list[dict]:
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("link", ""),
            "snippet": r.get("snippet", ""),
            "date": r.get("date", ""),
            "source": "news",
        }
        for r in results.get("news", [])
        if r.get("title")
    ]


def _parse_paa(results: dict) -> list[str]:
    return [item.get("question", "") for item in results.get("peopleAlsoAsk", []) if item.get("question")]


def _parse_related(results: dict) -> list[str]:
    return [item.get("query", "") for item in results.get("relatedSearches", []) if item.get("query")]


def run_scout(topic: str, api_key: str, progress_callback=None) -> dict:
    """
    Run full keyword-based research across all sources.
    Returns structured data organised by source type.
    """
    data = {
        "web_results": [],
        "reddit_results": [],
        "linkedin_results": [],
        "news_results": [],
        "review_results": [],
        "twitter_results": [],
        "forum_results": [],
        "people_also_ask": [],
        "related_searches": [],
        "related_terms": [],
    }

    def log(msg):
        if progress_callback:
            progress_callback(msg)

    # 1. Web search — also grabs PAA and related searches
    log("Searching Google...")
    raw = _serper_search(topic, api_key, num=10)
    data["web_results"] = _parse_organic(raw, "web")
    data["people_also_ask"] = _parse_paa(raw)
    data["related_searches"] = _parse_related(raw)
    data["related_terms"] = list(dict.fromkeys(data["related_searches"] + data["people_also_ask"]))

    # 2. Reddit
    log("Searching Reddit discussions...")
    raw_reddit = _serper_search(f"site:reddit.com {topic}", api_key, num=10)
    data["reddit_results"] = _parse_organic(raw_reddit, "reddit")

    # 3. LinkedIn posts and articles
    log("Searching LinkedIn...")
    raw_li = _serper_search(
        f'site:linkedin.com/posts OR site:linkedin.com/pulse {topic}',
        api_key, num=8
    )
    data["linkedin_results"] = _parse_organic(raw_li, "linkedin")

    # 4. Industry news
    log("Searching industry news...")
    raw_news = _serper_search(topic, api_key, num=10, endpoint=SERPER_NEWS_URL)
    data["news_results"] = _parse_news(raw_news)

    # 5. User reviews — G2, Capterra, Trustpilot
    log("Searching reviews (G2, Capterra, Trustpilot)...")
    raw_reviews = _serper_search(
        f'(site:g2.com OR site:capterra.com OR site:trustpilot.com) {topic}',
        api_key, num=8
    )
    data["review_results"] = _parse_organic(raw_reviews, "review")

    # 6. X / Twitter
    log("Searching X (Twitter)...")
    raw_tw = _serper_search(f"site:twitter.com OR site:x.com {topic}", api_key, num=8)
    data["twitter_results"] = _parse_organic(raw_tw, "twitter")

    # 7. Forums and discussion boards
    log("Searching forums & discussions...")
    raw_forums = _serper_search(f"{topic} forum discussion", api_key, num=8)
    # Filter out Reddit duplicates
    reddit_urls = {r["url"] for r in data["reddit_results"]}
    data["forum_results"] = [
        r for r in _parse_organic(raw_forums, "forum")
        if r["url"] not in reddit_urls and "reddit.com" not in r["url"]
    ]

    return data
