"""
Claude Strategist Module
Takes gap analysis + scout data and generates a full content brief
with inline recommendations using Claude.
"""
import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a senior content strategist who also knows how to write.
You write like a sharp, experienced blogger — the kind of person who's been in the trenches, not a textbook author or a corporate deck presenter.

Your briefs feel like a creative director sitting down with a writer over coffee and saying:
"Here's what this piece needs to be, here's why it'll work, and here's exactly how to open each section."

Your rules:
- Be direct and conversational. Write TO the writer, not at them.
- Never use filler phrases: "it's worth noting", "in today's digital landscape", "in conclusion", "leverage", "utilize", "comprehensive guide".
- Short sentences. Active voice. Real talk.
- Headings in your brief should be examples of what good headings look like — specific, human, keyword-rich. Think Backlinko, Wait But Why, James Clear, not Wikipedia.
- Every section suggestion should feel clickable and useful, not generic."""


def build_prompt(
    topic: str,
    gap_summary: str,
    competitor_titles: list[str],
    power_words: str = "",
    scout_data: dict | None = None,
) -> str:
    competitor_list = "\n".join(f"- {t}" for t in competitor_titles if t)

    # Build rich Reddit section from scout data
    reddit_block = ""
    if scout_data and scout_data.get("reddit_results"):
        reddit_lines = []
        for r in scout_data["reddit_results"][:8]:
            snippet = r.get("snippet", "").strip()
            title = r.get("title", "").strip()
            if title:
                reddit_lines.append(f'  • "{title}"')
            if snippet:
                reddit_lines.append(f'    → {snippet[:300]}')
        if reddit_lines:
            reddit_block = "## Real Reddit Conversations (use these verbatim where relevant)\n" + "\n".join(reddit_lines)

    # PAA questions
    paa_block = ""
    if scout_data and scout_data.get("people_also_ask"):
        questions = "\n".join(f"- {q}" for q in scout_data["people_also_ask"])
        paa_block = f"## Questions Real People Are Googling\n{questions}"

    # Web snippets for stat/context sourcing
    web_block = ""
    if scout_data and scout_data.get("web_results"):
        web_lines = []
        for r in scout_data["web_results"][:5]:
            snippet = r.get("snippet", "").strip()
            title = r.get("title", "").strip()
            if title and snippet:
                web_lines.append(f'  • [{title}]: "{snippet[:200]}"')
        if web_lines:
            web_block = "## What's Currently Ranking (snippets for context)\n" + "\n".join(web_lines)

    # Power words block
    power_words_block = ""
    if power_words and power_words.strip():
        power_words_block = f"""## Power Words to Use in Titles
Use these words when generating title options — pick the ones that match the emotional hook:
{power_words.strip()}
"""

    return f"""Here's the topic and all the research. Write the content brief for this.

## Topic
{topic}

## What Competitors Are Titling Their Articles
{competitor_list}

{power_words_block}
{reddit_block}

{paa_block}

{web_block}

## Full Competitive Gap Analysis
{gap_summary}

---

Now write the content brief. Structure it exactly like this:

---

## The Story (Angle + Hook)

In 2-3 sentences: what's the real angle here? What's the thing readers haven't seen before?
Then write the hook — the opening move for this article. Could be a surprising stat, a relatable frustration, a counterintuitive claim. Make it something a writer can actually use as their first line.

Also answer: who is this reader? What are they frustrated about right now? What do they already believe that this article needs to either confirm or challenge?

---

## Title Options

Give 3 title options. Each must:
- Include the target keyword naturally
- Use at least one power word (from the list above, if provided — otherwise use strong verbs and emotional words)
- Have a different emotional hook (e.g. one is curiosity-gap, one is benefit-led, one is challenge/contrarian)
- Sound like something a real blogger would write, not an AI

Format each like:
**Option 1 — [emotional hook type]:** [Title here]
*Why this works:* [one sentence]

---

## The Outline

Write a full H2/H3 structure. For each H2 section:

**[H2 heading — write it like a human, not a textbook. Make it specific and clickable.]**
*What this section does for the reader:* [one sentence — what problem does it solve or question does it answer?]
*Opening move:* [suggest a specific way to open this section — a stat, a story, a provocative question, a real quote from Reddit if relevant]
*What to actually write here:* [3-5 bullet points of specific things to cover — not "discuss X" but "explain WHY X happens and what most people get wrong about it"]

Then add any of these callouts where relevant:
→ [ADD STAT: describe exactly what kind of data would land here — e.g. "a study showing how many people X" or "a percentage showing Y"]
→ [PERSONAL EXAMPLE: e.g. "share a time when you made this mistake yourself" or "walk through a real client example where this happened"]
→ [REDDIT VOICE: pull in this exact quote or pain point from the Reddit data — put the actual snippet here so the writer can reference it]

Annotate each H2 with one tag on the same line as the heading:
`[MUST COVER]` — all competitors cover this, you need to too
`[GAP]` — competitors miss this, real opportunity
`[DIFFERENTIATOR]` — your unique angle, nobody else is doing this
`[USER QUESTION]` — directly answers something people are Googling

Include H3s under each H2 where the section needs sub-sections. H3s should also sound human and specific.

---

## The Voice Guide

5 bullet points on how to write this specific article:
- What tone to strike (e.g. "write like you're explaining this to a smart friend who knows nothing about the topic")
- What to avoid saying (give actual examples of phrases to ban)
- How to handle jargon
- What kind of examples and proof to reach for
- What the reader should feel at the end

---

## Keywords to Weave In

List the top 15 keywords/phrases from the research, and for each one say: which section it belongs in and how to use it naturally (don't keyword-stuff, show where it fits in a sentence).

---

## What to Steal From Competitors (Don't Skip These)

3-5 specific things competitors do well that you need to match or beat. Be specific — don't say "they cover X topic", say "Competitor A opens with Y and it works because Z."

---

## Before You Publish — 10-Point Checklist

A punchy, specific checklist. Not generic SEO advice. Things specific to this article and this topic. Things a writer could actually check off.

---

Be specific. Reference actual findings. Sound like a person, not a report generator."""


def generate_brief(
    topic: str,
    gap_summary: str,
    competitor_titles: list[str],
    api_key: str,
    power_words: str = "",
    scout_data: dict | None = None,
    progress_callback=None,
) -> tuple[str | None, str | None]:
    """
    Generate a content brief using Claude.
    Returns (brief_text, error).
    """
    try:
        client = Anthropic(api_key=api_key)
        prompt = build_prompt(topic, gap_summary, competitor_titles, power_words, scout_data)

        if progress_callback:
            progress_callback("Claude is reading the research and writing your brief...")

        message = client.messages.create(
            model=MODEL,
            max_tokens=8000,
            temperature=0.7,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        return message.content[0].text, None

    except Exception as e:
        logger.error(f"Claude strategist failed: {e}")
        return None, str(e)
