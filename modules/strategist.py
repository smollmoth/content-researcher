"""
Claude Strategist Module
Takes keyword research data and generates a Resource Bank + Content Brief.
"""
import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You're a senior content strategist. Your job is to turn raw keyword research into two things:
1. A usable Resource Bank — organised findings a writer can pull from directly
2. A Content Brief — strategic guide for the article

Tone: direct, specific, opinionated. No filler. No "it's worth noting". No "leverage".

**For the Resource Bank:**
- Pull out real quotes, real stats, real pain points from the research — not summaries
- Attribute everything: where it came from (Reddit, news, G2, LinkedIn, etc.)
- Flag the best ones clearly. A writer should be able to paste these straight into a draft.

**For the Content Brief:**
- H2s and H3s = real blog headings, ready to publish. Not labels.
- Be opinionated about what to cover and what to skip.
- Inline callouts at the exact point they apply:
  💬 Reddit: "[real quote]"
  [STAT: what kind, what it should prove]
  [ADD EXAMPLE: what kind]
  🔗 Link: [topic]

**Power words for titles:**
New, Free, Discover, Secret, Powerful, Top, Best, Latest, Ultimate, How to, Easy, Simple,
Step-by-step, Proven, Expert, Hidden, Revealed, Insider, Little-known, Quick, Blueprint,
Roadmap, Cheat sheet, Guaranteed, Results, Case study, Exclusive, Tested

**Before writing — search the web for real stats and studies on the keyword. Drop source URLs inline.**"""


def _build_prompt(topic: str, scout_data: dict, power_words: str = "") -> str:
    lines = []

    # Related terms / keyword cluster
    related = scout_data.get("related_terms", [])
    if related:
        lines.append("## Keyword Cluster")
        for t in related[:15]:
            lines.append(f"- {t}")
        lines.append("")

    # PAA
    paa = scout_data.get("people_also_ask", [])
    if paa:
        lines.append("## Questions People Are Googling (PAA)")
        for q in paa:
            lines.append(f"- {q}")
        lines.append("")

    # Reddit
    reddit = scout_data.get("reddit_results", [])
    if reddit:
        lines.append("## Reddit Discussions")
        for r in reddit[:8]:
            lines.append(f'**{r["title"]}**')
            if r.get("snippet"):
                lines.append(f'  → {r["snippet"][:400]}')
            lines.append(f'  URL: {r["url"]}')
        lines.append("")

    # LinkedIn
    linkedin = scout_data.get("linkedin_results", [])
    if linkedin:
        lines.append("## LinkedIn Posts & Articles")
        for r in linkedin[:6]:
            lines.append(f'**{r["title"]}**')
            if r.get("snippet"):
                lines.append(f'  → {r["snippet"][:300]}')
        lines.append("")

    # News
    news = scout_data.get("news_results", [])
    if news:
        lines.append("## Industry News")
        for r in news[:8]:
            date = f' ({r["date"]})' if r.get("date") else ""
            lines.append(f'**{r["title"]}**{date}')
            if r.get("snippet"):
                lines.append(f'  → {r["snippet"][:300]}')
            lines.append(f'  URL: {r["url"]}')
        lines.append("")

    # Reviews
    reviews = scout_data.get("review_results", [])
    if reviews:
        lines.append("## User Reviews (G2 / Capterra / Trustpilot)")
        for r in reviews[:6]:
            lines.append(f'**{r["title"]}**')
            if r.get("snippet"):
                lines.append(f'  → {r["snippet"][:300]}')
        lines.append("")

    # Twitter / X
    twitter = scout_data.get("twitter_results", [])
    if twitter:
        lines.append("## X / Twitter Discussions")
        for r in twitter[:6]:
            lines.append(f'**{r["title"]}**')
            if r.get("snippet"):
                lines.append(f'  → {r["snippet"][:200]}')
        lines.append("")

    # Forums
    forums = scout_data.get("forum_results", [])
    if forums:
        lines.append("## Forum & Discussion Boards")
        for r in forums[:6]:
            lines.append(f'**{r["title"]}**')
            if r.get("snippet"):
                lines.append(f'  → {r["snippet"][:300]}')
        lines.append("")

    # Web snippets
    web = scout_data.get("web_results", [])
    if web:
        lines.append("## Top-Ranking Web Pages (for context)")
        for r in web[:6]:
            lines.append(f'**{r["title"]}** — {r["url"]}')
            if r.get("snippet"):
                lines.append(f'  → {r["snippet"][:200]}')
        lines.append("")

    # Power words
    if power_words and power_words.strip():
        lines.append(f"## Power Words for Titles\n{power_words.strip()}\n")

    research_block = "\n".join(lines)

    return f"""Keyword: **{topic}**

Here's the raw research collected across sources:

{research_block}

---

Write two sections:

---

# PART 1 — RESOURCE BANK

A curated set of datapoints the writer can reference directly. Organise by source type. For each item worth keeping, include:
- The actual quote, stat, or insight (not a paraphrase — the real thing)
- Where it came from
- Why it's useful / where in the article it fits

Use these categories:
**Data & Studies** — stats, reports, original research worth citing
**Industry News** — recent developments that give the article timeliness
**Reddit & Forum Voice** — real user language, pain points, frustrations
**LinkedIn & Practitioner Takes** — expert angles, thought leadership
**Review Insights (G2 / Capterra / Trustpilot)** — user complaints and praise in their own words
**X / Twitter Angles** — niche takes, debate, breaking angles

Flag the top 3 most useful finds with ⭐

---

# PART 2 — CONTENT BRIEF

## Keyword Cluster

List: the primary keyword + all related terms worth targeting in this article (pulled from the research above). Mark the primary. Flag which ones belong in H2s, which in H3s, which as body mentions only.

---

## Funnel Stage

Auto-detect ToFu / MoFu / BoFu. One sentence on what that means for this article specifically:
- Writer's job (educate, compare, convert)?
- CTAs — how hard to push?
- What does the reader need next after this?

---

## ICP Snapshot

3-4 tight bullets:
- Job title or situation (specific, not "marketers")
- The exact problem that triggered the search today
- What they've already tried that didn't work
- What they need to believe by the end to take the next step

---

## 1. Search Intent & SERP Strategy

- **Intent:** What is the reader trying to DO? (specific)
- **Format Google rewards:** step-by-step, listicle, deep explainer, comparison? Why?
- **Content depth:** What's the minimum to compete? Where to go deeper?
- **Reader's real frustration:** What has nobody told them clearly yet?

---

## 2. Title, Meta & URL

**H1 options — give 3:**
Each must use at least one power word, include the keyword naturally, and have a different emotional hook. Under 60 chars each.

Format:
**Option 1 — [hook type]:** [Title]
*Why this works:* [one sentence]

**Title tag:** (max 60 chars, keyword near front)
**Meta description:** (max 155 chars — benefit or CTA, doesn't just repeat title)
**URL slug:** (short, keyword-first, no stop words)

---

## 3. Opening Paragraph Options

2 actual draft openings the writer can steal:
- Option A: surprising stat or counterintuitive claim
- Option B: relatable frustration or scenario

Sound human. Get to the point in sentence one.

---

## 4. The Outline

Full H2/H3 structure. Every heading = real blog heading, ready to publish.

**For each H2:**

**[Real heading]** `[TAG]`
*Payoff:* [one line]
*~X words* | *Open with:* [stat / Reddit quote / question]
- [specific thing to write — WHY it matters]
- [specific thing to write]

Inline callouts at the exact bullet where they apply:
- 💬 Reddit: "[real quote from the research above]"
- [STAT: what kind, what it should prove]
- [ADD EXAMPLE: what kind and why]
- `[AUTHORITY: entities Google expects here]`
- `[KEYWORD: secondary keyword for this section]`
- `[SNIPPET TARGET: format for: "exact PAA question"]`
- `[EEAT: experience/expertise/trust — what specifically]`
- `[STEAL: what competitors do well here]`
- `[BEAT: competitor weakness to exploit]`
- 🔗 Link: [internal topic and why]
- > [brand/product angle bullet]

Tags (same line as H2):
`[MUST COVER]` `[GAP]` `[DIFFERENTIATOR]` `[USER QUESTION]`

---

## 5. Voice Guide

5 tight bullets — like a sticky note on the writer's monitor:
- Tone: one analogy
- Phrases banned: 3 real examples from how this topic usually gets written
- Jargon: is the audience fluent or not, what's the rule?
- Proof to reach for first: data, story, expert quote, or Reddit voice — and why for THIS topic
- Last line goal: what the reader thinks, feels, or does differently after finishing

---

## 6. Pre-Publish Checklist

12 items specific to this article. At least 3 target gaps in the current SERP. Things a writer can literally check off.

Include:
☐ [INTERNAL LINK OPPORTUNITY: link to article on [most relevant sub-topic] — builds topical authority]
☐ [INTERNAL LINK OPPORTUNITY: link to article on [second related topic from reader journey]]
Plus: schema type (Article / HowTo / FAQ / Review — why), hero image alt text with primary keyword, total target word count.

---

End with one sentence: the single most important thing that will determine whether this article ranks."""


def generate_brief(
    topic: str,
    scout_data: dict,
    api_key: str,
    power_words: str = "",
    progress_callback=None,
) -> tuple[str | None, str | None]:
    """
    Generate a Resource Bank + Content Brief using Claude.
    Returns (brief_text, error).
    """
    try:
        client = Anthropic(api_key=api_key)
        prompt = _build_prompt(topic, scout_data, power_words)

        if progress_callback:
            progress_callback("Claude is reading the research and building your resource bank + brief...")

        message = client.messages.create(
            model=MODEL,
            max_tokens=8000,
            temperature=0.7,
            system=SYSTEM_PROMPT,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": prompt}],
        )

        text = "\n\n".join(b.text for b in message.content if hasattr(b, "text") and b.text.strip())
        return text or None, None

    except Exception as e:
        logger.error(f"Claude strategist failed: {e}")
        return None, str(e)
