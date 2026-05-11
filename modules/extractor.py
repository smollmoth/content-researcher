"""
Content Extractor Module
Scrapes competitor URLs and extracts clean text content, H1, and title.
"""
import requests
from bs4 import BeautifulSoup
import random
import time
import logging

logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}


def fetch_page(url: str, timeout: int = 15) -> tuple[str | None, str | None]:
    """Fetch raw HTML from a URL."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        return response.text, None
    except requests.RequestException as e:
        return None, str(e)


def extract_h1(soup: BeautifulSoup) -> str | None:
    tag = soup.find('h1')
    return tag.get_text(strip=True) if tag else None


def extract_title(soup: BeautifulSoup) -> str | None:
    tag = soup.find('title')
    return tag.get_text(strip=True) if tag else None


def extract_headings(soup: BeautifulSoup) -> list[str]:
    """Extract all headings (H1-H3) to understand content structure."""
    headings = []
    for tag in soup.find_all(['h1', 'h2', 'h3']):
        text = tag.get_text(strip=True)
        if text:
            headings.append(f"{tag.name.upper()}: {text}")
    return headings


def html_to_text(soup: BeautifulSoup) -> str:
    """Convert parsed HTML to clean plain text."""
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript']):
        tag.decompose()
    for br in soup.find_all('br'):
        br.replace_with('\n')
    for el in soup.find_all(['p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'div']):
        el.append('\n\n')
    text = soup.get_text(separator=' ')
    return ' '.join(text.split())


def scrape_url(url: str, rate_limit: float = 1.0) -> dict:
    """Scrape a single URL and return structured content."""
    time.sleep(random.uniform(rate_limit * 0.5, rate_limit * 1.5))
    html, error = fetch_page(url)

    if not html:
        return {
            'url': url,
            'title': None,
            'h1': None,
            'headings': [],
            'content': None,
            'content_length': 0,
            'status': 'Failed',
            'error': error
        }

    soup = BeautifulSoup(html, 'html.parser')
    content = html_to_text(soup)

    return {
        'url': url,
        'title': extract_title(soup),
        'h1': extract_h1(soup),
        'headings': extract_headings(soup),
        'content': content,
        'content_length': len(content),
        'status': 'Success',
        'error': None
    }


def scrape_urls(urls: list[str], rate_limit: float = 1.0, progress_callback=None) -> list[dict]:
    """Scrape multiple URLs sequentially with optional progress updates."""
    results = []
    for i, url in enumerate(urls):
        result = scrape_url(url, rate_limit)
        results.append(result)
        if progress_callback:
            progress_callback(i + 1, len(urls), url)
    return results
