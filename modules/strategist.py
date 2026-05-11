"""
Claude Strategist Module
Takes gap analysis + scout data and generates a full content brief
with inline recommendations using Claude.
"""
import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You're a senior SEO strategist briefing a smart writer over Slack. Not writing a strategy doc — sending notes.

Tone: casual, direct, short bullets. Like a colleague who knows what they're doing and respects the writer's time.

**How the output should feel:**
- Conversational. First person where it helps. "Skip this if..." / "Do NOT do..." / "This one matters a lot."
- Tight bullets, not paragraphs. If you catch yourself writing 3 sentences, cut to 1.
- Opinionated. Say what will work and what won't. No hedging.
- Never: "it's worth noting", "in today's digital landscape", "leverage", "utilize", "comprehensive guide", "delve".

**H2s and H3s in the outline = real blog headings only.**
Write them as if they're going live on the page. Human, natural, keyword-rich, clickable.
NOT labels like "Topical Authority Map" or "Section 3: Overview".
Think Backlinko, Ahrefs Blog, James Clear. "Why Your X Keeps Failing (And the Fix Nobody Talks About)" — that kind of thing.

**Power words to use naturally in title options and headings:**
New, Free, Discover, Secret, Powerful, Top, Best, Latest, Ultimate, How to, Easy, Simple,
Step-by-step, Proven, Expert, Hidden, Revealed, Insider, Little-known, Quick, Instantly,
Blueprint, Roadmap, Cheat sheet, Guaranteed, Results, Case study, Exclusive, Tested

**Inline callouts — use these inside the outline, at the exact point they apply:**
- 💬 Reddit: "[quote]" — real language patterns from Reddit threads on this topic. Find actual quotes.
- [STAT: find one about X] — flag where a specific stat is needed and what it should prove
- [ADD EXAMPLE: what type] — flag where a personal example or case study would hit hardest, and why
- 🔗 Link: [topic] — internal link suggestion, placed where it's actually relevant

**Brand/product angles:**
When a bullet is a brand or product recommendation angle, lead it with >

**Before writing the outline:** search the web for real stats, studies, and Reddit threads on the keyword. Drop real source URLs inline where you found data: 🔗 Source: [url]"""


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

## Funnel Stage

Auto-detect: is this ToFu, MoFu, or BoFu based on the keyword?
Write one sentence — what that means for THIS article specifically:
- What's the writer's job here (educate, compare, convert)?
- Should there be CTAs? How hard to push the product angle?
- What does the reader need NEXT after this article?

---

## ICP Snapshot

Based on the keyword and research, describe who is most likely searching this.
Cover in 3-4 tight bullets:
- Their job title or situation (be specific — not "marketers", say "solo founders running paid ads" or "HR managers at 50-person startups")
- The exact problem they're trying to solve RIGHT NOW — not the topic in general, but what triggered the search today
- What they've probably already tried that didn't work
- What they need to believe by the end of the article to take the next step

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
Each title MUST use at least one power word from this list:
New, Free, Discover, Secret, Powerful, Top, Best, Latest, Ultimate, How to, Easy, Simple, Step-by-step, Proven, Expert, Hidden, Revealed, Insider, Little-known, Quick, Instantly, Blueprint, Roadmap, Cheat sheet, Guaranteed, Results, Case study, Exclusive, Tested

Each must also include the target keyword naturally and have a different emotional hook. Keep each title under 60 characters. Write them like a human headline writer, not an AI.

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

Full H2/H3 structure. Every heading = a real blog heading, ready to publish. Not a label, not a placeholder.

Everything the writer needs lives inside this outline. Do not save authority notes, E-E-A-T signals, snippet targets, keyword placements, or competitor intel for a separate section — drop each one as an inline callout at the exact H2/H3 it belongs to.

**For each H2:**

**[Real blog heading — human, keyword-rich, clickable]** `[TAG]`
*Payoff:* [one line — what does the reader walk away with?]
*~X words* | *Open with:* [stat / Reddit quote / question / micro-story]
- [specific thing to write — WHY it matters, what most people get wrong]
- [specific thing to write]
- [specific thing to write]

**Inline callouts — drop at the exact bullet where they apply:**

Content callouts:
- 💬 Reddit: "[real quote or language pattern from an actual thread]"
- [STAT: what kind of data would land here and what it should prove]
- [ADD EXAMPLE: what kind — "a brand that tried X" / "someone who did Z and saw Y result"]

SEO & authority callouts (place inside each H2 where they apply — not at the end):
- `[AUTHORITY: term1, term2, term3]` — entities and terms Google expects to see in this section to treat the page as authoritative; if skipped, topical coverage looks thin
- `[KEYWORD: secondary keyword to use naturally here]` — keyword placement instruction for this section
- `[SNIPPET TARGET: format as numbered list / definition box / table for: "exact PAA question"]` — format the opening of this section to win this featured snippet
- `[EEAT: experience — add a first-hand anecdote here about X]` or `[EEAT: expertise — cite a study / official body on Y here]` or `[EEAT: trust — add a disclaimer / date stamp / methodology note here]`

Competitor callouts:
- `[STEAL: competitors do X well here — match it by doing Y]`
- `[BEAT: competitor weakness — they're thin/wrong/missing Z here; exploit it by doing W]`

Link callouts:
- 🔗 Link: [internal topic to link to, and why it fits here]
- > [brand or product angle bullet — leads with > when it's a recommendation or commercial angle]

**Tags (same line as H2 heading):**
`[MUST COVER]` — skip it and you lose to competitors
`[GAP]` — competitors miss this, real opportunity
`[DIFFERENTIATOR]` — your angle, nobody else doing this
`[USER QUESTION]` — directly answers a PAA or Reddit question

H3s under each H2 where the section needs sub-points. Write H3s as real clickable headings — "The 3 types that actually matter (and the ones to ignore)", not "Types of X". Apply the same inline callouts inside H3s where relevant.

---

## 5. Voice Guide

5 bullets. No headers. Write it like a sticky note on the writer's monitor — not a style guide.
- Tone: one analogy ("write like you're explaining to a [specific type of person]...")
- Phrases banned on this piece: give 3 real examples pulled from how competitors write it
- How to handle jargon: is this audience fluent or not, and what's the rule?
- What proof to reach for first: data, personal story, expert quote, or Reddit voice — and why for THIS topic
- Last line goal: one sentence on what the reader should think, feel, or do differently after finishing

---

## 6. Pre-Publish Ranking Checklist

12 items. Not generic SEO — specific to this article and topic. Things a writer can literally check off before hitting publish. At least 3 must target gaps competitors are missing.

Include these 2 internal link items (fill in the bracketed topic based on the keyword):
☐ [INTERNAL LINK OPPORTUNITY: link to your article on [most relevant sub-topic from this keyword cluster] here — builds topical authority and keeps the reader on site]
☐ [INTERNAL LINK OPPORTUNITY: link to your article on [second related topic that naturally follows from this article's reader journey] here — builds topical authority and keeps the reader on site]

Also include: schema type recommendation (Article / HowTo / FAQ / Review — and why), hero image alt text suggestion using the primary keyword, and total target word count based on competitor depth.

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

        # Web search produces interleaved text + tool_use blocks; join all text blocks in order
        text = "\n\n".join(b.text for b in message.content if hasattr(b, "text") and b.text.strip())
        return text or None, None

    except Exception as e:
        logger.error(f"Claude strategist failed: {e}")
        return None, str(e)
