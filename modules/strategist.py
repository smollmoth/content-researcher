"""
Claude Strategist Module
Takes gap analysis + scout data and generates a full content brief
with inline recommendations using Claude.
"""
import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"


def build_prompt(topic: str, gap_summary: str, competitor_titles: list[str]) -> str:
    competitor_list = '\n'.join(f"- {t}" for t in competitor_titles if t)
    return f"""You are a senior content strategist. A writer wants to create a comprehensive, authoritative article on the topic below.
You have been given a full analysis of what the top competitors cover. Your job is to produce a detailed content brief that will help the writer create something better than all competitors combined.

## Topic
{topic}

## Competitor Titles Found
{competitor_list}

## Full Competitive Gap Analysis
{gap_summary}

---

Based on the above, produce a structured content brief with these sections:

## 1. Content Angle & Positioning
- What unique angle should this article take?
- What makes it stand out from competitors?
- Who is the target reader?

## 2. Recommended Title Options (3 options)
- Give 3 strong title options with different angles

## 3. Suggested Article Structure
- Full outline with H2s and H3s
- For each section: what to cover and why competitors miss it or do it poorly
- Annotate each section with one of:
  <!-- MUST COVER: all competitors cover this, you need to too -->
  <!-- GAP: competitors miss this, big opportunity -->
  <!-- DIFFERENTIATOR: unique angle to stand out -->
  <!-- USER QUESTION: real question people are asking -->

## 4. Key Topics & Keywords to Include
- List the most important terms and phrases to naturally include
- Group by theme/section

## 5. What Competitors Do Well (Don't Miss This)
- Common strengths across competitor content you must match

## 6. What Competitors Miss (Your Opportunity)
- Clear gaps in competitor coverage
- Questions left unanswered
- Angles nobody is taking

## 7. Reddit & Community Insights
- Key pain points, questions, and language from real users
- How to address these in the article

## 8. Quick Wins Checklist
A checklist of the most important things to include for this article to outperform competitors.

Be specific, actionable, and reference actual findings from the gap analysis. Do not be generic."""


def generate_brief(
    topic: str,
    gap_summary: str,
    competitor_titles: list[str],
    api_key: str,
    progress_callback=None
) -> tuple[str | None, str | None]:
    """
    Generate a content brief using Claude.
    Returns (brief_text, error).
    """
    try:
        client = Anthropic(api_key=api_key)
        prompt = build_prompt(topic, gap_summary, competitor_titles)

        if progress_callback:
            progress_callback("Claude is analyzing the research...")

        message = client.messages.create(
            model=MODEL,
            max_tokens=8000,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}]
        )

        return message.content[0].text, None

    except Exception as e:
        logger.error(f"Claude strategist failed: {e}")
        return None, str(e)
