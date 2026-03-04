"""
Scout Module
Searches the web and Reddit for topic discussions, questions, and angles
using the Serper.dev API.
"""
import requests
import logging

logger = logging.getLogger(__name__)

SERPER_URL = "https://google.serper.dev/search"


def _serper_search(query: str, api_key: str, num: int = 10, search_type: str = "search") -> dict:
    """Run a search query via Serper API."""
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "q": query,
        "num": num
    }
    try:
        response = requests.post(SERPER_URL, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Serper search failed for '{query}': {e}")
        return {}


def _parse_organic(results: dict) -> list[dict]:
    """Extract organic search results."""
    items = results.get('organic', [])
    return [
        {
            'title': r.get('title', ''),
            'url': r.get('link', ''),
            'snippet': r.get('snippet', ''),
            'source': 'web'
        }
        for r in items
    ]


def _parse_people_also_ask(results: dict) -> list[str]:
    """Extract 'People Also Ask' questions."""
    return [
        item.get('question', '')
        for item in results.get('peopleAlsoAsk', [])
        if item.get('question')
    ]


def _parse_related_searches(results: dict) -> list[str]:
    """Extract related search queries."""
    return [
        item.get('query', '')
        for item in results.get('relatedSearches', [])
        if item.get('query')
    ]


def search_web(topic: str, api_key: str, num: int = 10) -> list[dict]:
    """Search the open web for a topic."""
    results = _serper_search(topic, api_key, num=num)
    return _parse_organic(results)


def search_reddit(topic: str, api_key: str, num: int = 10) -> list[dict]:
    """Search Reddit discussions for a topic via Serper."""
    query = f"site:reddit.com {topic}"
    results = _serper_search(query, api_key, num=num)
    items = _parse_organic(results)
    for item in items:
        item['source'] = 'reddit'
    return items


def get_people_also_ask(topic: str, api_key: str) -> list[str]:
    """Get 'People Also Ask' questions for a topic."""
    results = _serper_search(topic, api_key, num=10)
    return _parse_people_also_ask(results)


def get_related_searches(topic: str, api_key: str) -> list[str]:
    """Get related searches for a topic."""
    results = _serper_search(topic, api_key, num=10)
    return _parse_related_searches(results)


def run_scout(topic: str, api_key: str, progress_callback=None) -> dict:
    """
    Run full scout research for a topic.
    Returns web results, Reddit discussions, PAA questions, and related searches.
    """
    scout_data = {
        'web_results': [],
        'reddit_results': [],
        'people_also_ask': [],
        'related_searches': []
    }

    if progress_callback:
        progress_callback("Searching the web...")
    raw = _serper_search(topic, api_key, num=10)
    scout_data['web_results'] = _parse_organic(raw)
    scout_data['people_also_ask'] = _parse_people_also_ask(raw)
    scout_data['related_searches'] = _parse_related_searches(raw)

    if progress_callback:
        progress_callback("Searching Reddit discussions...")
    scout_data['reddit_results'] = search_reddit(topic, api_key, num=10)

    return scout_data
