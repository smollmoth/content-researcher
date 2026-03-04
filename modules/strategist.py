"""
Claude Strategist Module
Takes gap analysis + scout data and generates a full content brief
with inline recommendations using Claude.
"""
import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a senior SEO content strategist who's shipped hundreds of articles that actually rank.
You know that ranking and quality aren't in conflict — Google rewards the article that best answers the reader's real question, with real depth, real experience, and real structure.

Your briefs are the ones writers actually use. They're specific, opinionated, and honest about what will and won't work.
You write TO the writer, like a colleague who's done this before and wants them to succeed.

Your non-negotiables:
- Ranking is the primary goal. A great article nobody finds is a wasted article.
- Every recommendation is grounded in what the SERP data and competitor research actually shows.
- Headings must be human and clickable — think Backlinko, James Clear, Ahrefs Blog. Never "Introduction to X" or "Overview of Y".
- No filler. No "it's worth noting", "in today's digital landscape", "leverage", "utilize", "comprehensive".
- Short sentences. Active voice. Tell the writer what to DO, not what to "consider".

Before writing the outline, search the web for real stats, studies, and Reddit threads related to the keyword.
Drop real links to sources inline under each H3 where you found data. Label them: 🔗 Source: [url]
For Reddit quotes, find actual threads and quote real language patterns — label them: 💬 Reddit: [subreddit name]"""


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

    return f"""Here's the research. Write the content brief.

## Topic / Target Keyword
{topic}

## Competitor Titles (what's already ranking)
{competitor_list}

{power_words_block}
{reddit_block}

{paa_block}

{web_block}

## Full Competitive Gap Analysis
{gap_summary}

---

Write the content brief using this exact structure. Be specific — reference actual findings from the research above. Sound like a person, not a tool.

---

## 1. Search Intent & SERP Strategy

Answer these four things directly:
- **Intent:** What is the reader actually trying to DO? (learn, compare, buy, fix a problem?) Be specific — not just "informational".
- **Format Google rewards:** Based on what's ranking, what content format wins here — step-by-step guide, listicle, deep explainer, comparison, definition-first? Why?
- **Content depth needed:** Look at competitor word counts. What's the minimum to compete, and where should we go deeper than everyone else?
- **The reader's real frustration:** What has the reader already tried or read that didn't work? What do they want to know that nobody is telling them clearly?

---

## 2. Title, Meta & URL

**H1 options — give 3:**
Each must include the target keyword naturally, use at least one power word from the list, and have a different emotional hook.

Format:
**Option 1 — [hook type]:** [Title]
*Why this works:* [one sentence — what SERP gap or emotional trigger does this hit?]

**Title tag:** (can be shorter than H1 if needed — max 60 chars, keyword near the front)

**Meta description:** (max 155 chars — includes keyword, has a clear benefit or CTA, doesn't just repeat the title)

**URL slug:** (short, keyword-first, no stop words)

---

## 3. Opening Paragraph Options

Give 2 actual draft opening paragraphs the writer can steal or riff on.
- Option A: leads with a surprising stat or counterintuitive claim
- Option B: leads with a relatable frustration or scenario the reader recognises immediately

These should sound human. No "In today's world..." or "Have you ever wondered...". Get to the point in sentence one.

---

## 4. The Outline

Write the full H2/H3 structure. For each H2:

**[H2 heading]** `[TAG]`
*Reader payoff:* [what does the reader get from this section — not what it covers, but what it gives them]
*Word count target:* [~X words — base this on competitor depth for this topic]
*Opening move:* [specific suggestion — a stat, a quote from Reddit, a question, a micro-story]
*Write this:*
  - [specific point 1 — not "discuss X" but "show WHY X happens and what most people miss"]
  - [specific point 2]
  - [specific point 3]

Callouts (add where relevant):
→ `[SNIPPET TARGET]` — if a PAA question maps to this section, flag it: "Format as a [definition box / numbered list / table] to target the featured snippet for: '[exact question]'"
→ `[ADD STAT]` — describe the specific kind of data that would strengthen this: "a study on X" or "a % showing Y"
→ `[PERSONAL EXAMPLE]` — what kind of first-hand story or client case would land here
→ `[REDDIT VOICE]` — paste the actual Reddit quote or pain point that maps to this section so the writer can reference it

Tags for each H2 (put on same line as heading):
`[MUST COVER]` — all competitors have this; skip it and you lose
`[GAP]` — competitors miss this; big opportunity
`[DIFFERENTIATOR]` — your angle; nobody else is doing this
`[USER QUESTION]` — directly answers a PAA or Reddit question

H3s: use them where a section has 2+ distinct sub-points. Write H3s as human, specific, clickable — not "Types of X" but "The 3 types that actually matter (and the ones to ignore)".

---

## 5. Topical Authority Map

List the sub-topics, entities, and related terms this article MUST mention to be considered authoritative on the topic by Google.
Group them by theme. For each cluster, one sentence on why Google expects to see this if we're serious about this topic.

Format:
**[Theme/Cluster]:** term1, term2, term3 — *why this matters for topical coverage*

If you skip any of these, flag it: "Missing this signals to Google that this page doesn't fully cover the topic."

---

## 6. E-E-A-T Injection Points

Google needs to see Experience, Expertise, Authoritativeness, Trust. Tell the writer exactly where and how to inject each:

- **Experience:** Which sections should include first-hand anecdotes or direct observations? What kind of personal experience would be credible here?
- **Expertise:** Which claims need a citation? What types of sources does Google trust for this topic (studies, official bodies, recognised experts)?
- **Authority:** What should the author intro/bio say to establish credibility for this specific topic?
- **Trust:** Where should the writer add disclaimers, methodology notes, date stamps, or transparency signals?

---

## 7. SERP Feature Targets

Based on the PAA questions and query structure, list the specific featured snippet opportunities:

For each one:
- **Question:** [exact question]
- **Target format:** [definition box / numbered list / table / FAQ]
- **Where in the article:** [which H2/H3]
- **How to format it:** [e.g. "Open with a 40-60 word direct answer that starts with '{topic} is...' then expand below"]

---

## 8. On-Page SEO Placement Map

Tell the writer exactly where to place things:

- **Primary keyword** `{topic}`: H1 ✓, first 100 words ✓, at least one H2 ✓, meta description ✓, image alt text ✓
- **Secondary keywords:** list 5-8 and which H2 each belongs in
- **Hero image alt text:** suggest a specific alt text using the primary keyword naturally
- **Schema type:** recommend one — Article / HowTo / FAQ / Review / other — and why
- **Internal linking:** what topic clusters or related content this should link to (even if you don't know their exact URLs, describe the topic)
- **Total word count target:** based on competitor depths, what's the right length to be comprehensive without padding?

---

## 9. Competitor Intelligence — Steal & Beat

**Steal these (3-5 things competitors do well that you must match):**
Be specific. Not "they cover topic X" — say "Competitor A does Y in their intro and it works because Z. Do the same but go further by..."

**Beat these (3-5 specific competitor weaknesses to exploit):**
Where are the thin sections? The weak intros? The unanswered questions? Name them and say how to exploit each one.

---

## 10. The Voice Guide

5 bullets — how to write THIS article specifically:
- Tone (give an analogy: "write like you're explaining to a [type of person]...")
- Specific phrases to ban (give real examples based on how competitors write)
- How to handle jargon for this topic's audience
- What kind of proof to reach for first (data, stories, expert quotes, personal experience)
- What the reader should think/feel/do differently after reading the last line

---

## 11. Pre-Publish Ranking Checklist

10 specific, actionable items. Not generic SEO — things specific to this article and topic.
Things a writer can literally check off before hitting publish.
At least 3 of these should be things competitors are missing that this article needs to get right.

---

End with one sentence: the single most important thing that will determine whether this article ranks or not."""


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
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": prompt}],
        )

        # With tool use enabled, content is a list of blocks; extract the final text block
        text = next((b.text for b in reversed(message.content) if hasattr(b, "text")), None)
        return text, None

    except Exception as e:
        logger.error(f"Claude strategist failed: {e}")
        return None, str(e)
