"""
Gap Finder Module
The brain — analyzes competitor content to find:
- Common topics all competitors cover
- Unique angles only some cover
- Missing information gaps
- Key themes and subtopics
"""
import string
import logging
from collections import Counter
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import nltk
    from nltk.corpus import stopwords
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)
    STOP_WORDS = set(stopwords.words('english'))
except Exception:
    STOP_WORDS = {
        'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'can',
        'could', 'should', 'may', 'might', 'this', 'that', 'these', 'those',
        'it', 'its', 'as', 'if', 'so', 'we', 'you', 'he', 'she', 'they',
        'not', 'no', 'also', 'just', 'more', 'very', 'about', 'up', 'out'
    }


def preprocess(text: str) -> list[str]:
    """Clean text and return meaningful words."""
    if not isinstance(text, str):
        return []
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    return [w for w in text.split() if w not in STOP_WORDS and len(w) > 2]


def extract_ngrams(words: list[str], n: int = 2) -> list[str]:
    """Extract n-grams from word list."""
    return [' '.join(words[i:i+n]) for i in range(len(words) - n + 1)]


def analyze_competitor_content(competitor_results: list[dict]) -> dict:
    """
    Analyze extracted competitor content.
    Returns common topics, unique angles, and content gaps.
    """
    successful = [r for r in competitor_results if r.get('status') == 'Success' and r.get('content')]

    if not successful:
        return {
            'common_topics': [],
            'unique_topics': {},
            'all_keywords': [],
            'heading_themes': [],
            'coverage_by_competitor': {},
            'total_competitors_analyzed': 0
        }

    # Per-competitor word sets and counts
    competitor_word_data = []
    for result in successful:
        words = preprocess(result['content'])
        bigrams = extract_ngrams(words, 2)
        trigrams = extract_ngrams(words, 3)
        all_terms = words + bigrams + trigrams
        competitor_word_data.append({
            'url': result['url'],
            'title': result.get('title', ''),
            'h1': result.get('h1', ''),
            'headings': result.get('headings', []),
            'word_set': set(words),
            'term_counter': Counter(all_terms),
            'word_count': len(words)
        })

    n = len(competitor_word_data)

    # Find terms and how many competitors use them
    all_term_counts = Counter()
    term_competitor_count = Counter()
    for data in competitor_word_data:
        for term, count in data['term_counter'].items():
            all_term_counts[term] += count
            term_competitor_count[term] += 1

    # Common topics: appear in majority of competitors (>= 60%)
    threshold = max(2, round(n * 0.6))
    common_topics = [
        {'term': term, 'competitor_count': cnt, 'total_mentions': all_term_counts[term]}
        for term, cnt in term_competitor_count.most_common(100)
        if cnt >= threshold and len(term.split()) >= 1
    ]

    # Unique angles: terms only 1 competitor uses (could be differentiators)
    unique_topics = {}
    for data in competitor_word_data:
        unique = [
            term for term, cnt in data['term_counter'].items()
            if term_competitor_count[term] == 1 and cnt >= 2
        ]
        if unique:
            unique_topics[data['url']] = unique[:20]

    # All keywords sorted by frequency across all competitors
    all_keywords = [
        {'term': term, 'mentions': count, 'competitor_coverage': term_competitor_count[term]}
        for term, count in all_term_counts.most_common(50)
        if len(term) > 3
    ]

    # Heading themes across all competitors
    all_headings = []
    for data in competitor_word_data:
        all_headings.extend(data['headings'])

    # Coverage summary per competitor
    coverage_by_competitor = {
        data['url']: {
            'title': data['title'],
            'h1': data['h1'],
            'word_count': data['word_count'],
            'headings': data['headings']
        }
        for data in competitor_word_data
    }

    return {
        'common_topics': common_topics,
        'unique_topics': unique_topics,
        'all_keywords': all_keywords,
        'heading_themes': all_headings,
        'coverage_by_competitor': coverage_by_competitor,
        'total_competitors_analyzed': n
    }


def format_gap_summary(gap_analysis: dict, scout_data: Optional[dict] = None) -> str:
    """
    Format gap analysis into a readable summary string
    to pass to the Claude strategist.
    """
    lines = []
    n = gap_analysis['total_competitors_analyzed']
    lines.append(f"## Competitor Analysis Summary ({n} competitors analyzed)\n")

    # Common topics
    lines.append("### Topics All Competitors Cover")
    for item in gap_analysis['common_topics'][:20]:
        lines.append(f"- **{item['term']}** (in {item['competitor_count']}/{n} competitors, {item['total_mentions']} total mentions)")

    # Top keywords
    lines.append("\n### Top Keywords by Frequency")
    for item in gap_analysis['all_keywords'][:20]:
        lines.append(f"- {item['term']} ({item['mentions']} mentions, {item['competitor_coverage']}/{n} competitors)")

    # Heading themes
    if gap_analysis['heading_themes']:
        lines.append("\n### Competitor Content Structure (Headings)")
        for heading in gap_analysis['heading_themes'][:30]:
            lines.append(f"- {heading}")

    # Unique angles
    if gap_analysis['unique_topics']:
        lines.append("\n### Unique Angles (only used by one competitor)")
        for url, terms in gap_analysis['unique_topics'].items():
            lines.append(f"- **{url}**: {', '.join(terms[:10])}")

    # Scout data
    if scout_data:
        if scout_data.get('people_also_ask'):
            lines.append("\n### Questions People Are Asking (Google PAA)")
            for q in scout_data['people_also_ask']:
                lines.append(f"- {q}")

        if scout_data.get('related_searches'):
            lines.append("\n### Related Searches")
            for s in scout_data['related_searches']:
                lines.append(f"- {s}")

        if scout_data.get('reddit_results'):
            lines.append("\n### Reddit Discussions Found")
            for r in scout_data['reddit_results'][:5]:
                lines.append(f"- [{r['title']}]({r['url']})")
                if r.get('snippet'):
                    lines.append(f"  *{r['snippet'][:150]}*")

    return '\n'.join(lines)
