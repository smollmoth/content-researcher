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

For each H2:

**[Real blog heading — human, keyword-rich, clickable]** `[TAG]`
*Payoff:* [one line — what does the reader walk away with?]
*~X words* | *Open with:* [stat / Reddit quote / question / micro-story]
- [specific thing to write — WHY it matters, what most people get wrong]
- [specific thing to write]
- [specific thing to write]

Drop inline callouts at the exact bullet where they apply — not at the end:
- 💬 Reddit: "[real quote or language pattern from an actual thread]"
- [STAT: what kind of data would land here, e.g. "% of people who X" or "study on Y"]
- [ADD EXAMPLE: what kind of example — "a brand that tried X" / "someone who did Z and saw Y result"]
- 🔗 Link: [internal topic to link to, and why it fits here]
- `[SNIPPET TARGET: format as numbered list / definition box / table for: "exact PAA question"]`
- > [brand or product angle bullet — leads with > when it's a recommendation or commercial angle]

Tags (same line as H2 heading):
`[MUST COVER]` — skip it and you lose to competitors
`[GAP]` — competitors miss this, real opportunity
`[DIFFERENTIATOR]` — your angle, nobody else doing this
`[USER QUESTION]` — directly answers a PAA or Reddit question

H3s under each H2 where the section needs sub-points. Write H3s as real clickable headings too — "The 3 types that actually matter (and the ones to ignore)", not "Types of X".

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

        # Web search produces interleaved text + tool_use blocks; join all text blocks in order
        text = "\n\n".join(b.text for b in message.content if hasattr(b, "text") and b.text.strip())
        return text or None, None

    except Exception as e:
        logger.error(f"Claude strategist failed: {e}")
        return None, str(e)
