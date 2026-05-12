"""
Claude Strategist Module
Takes research data and generates a curated Resource Bank + editorial brief.
"""
import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a senior editorial strategist. You turn raw research into sharp editorial direction.

Your job: find the thesis, the tension, and the fresh angle — then build a brief that gives a writer something to argue, not a template to fill.

Tone: direct, opinionated, specific. No filler. No "it's worth noting". No "leverage". No "in today's fast-paced world".

**What you're NOT doing:**
- Writing SEO templates ("What is X", "Benefits of X", "How X Works")
- Listing keyword clusters for targeting
- Mapping funnel stages
- Producing FAQ outlines
- Dumping every stat you found

**What you ARE doing:**
- Finding the one argument this article should make
- Identifying the live debate or tension in this space
- Spotting what changed recently that makes this worth writing now
- Curating only the evidence that supports the argument — not everything you found
- Giving the writer a narrative direction, not a structure to fill

**On research curation:**
Before writing, search the web for the freshest stats, case studies, and expert takes on this topic. Drop source URLs inline. Prioritise findings from the last 12 months. Flag anything older than 2023 as potentially stale.

**Information gain rule:** If a point appears in every article on this topic, cut it. Only include what gives the reader something they couldn't get from the first Google result."""


def _build_article_improvement_section(article_content: str) -> str:
    truncated = article_content[:6000]
    return f"""---

# PART 3 — ARTICLE IMPROVEMENT SUGGESTIONS

Below is the existing article to update. Using the research above, compare what the article currently covers against the fresh evidence, debates, and angles you've surfaced.

**Existing article content:**
{truncated}

---

Provide a focused improvement brief with these sections:

## What the Article Gets Right
2-3 bullets. What's solid and should stay. Be specific.

## Outdated or Stale Content
Flag specific claims, stats, or sections that are now outdated based on the research. For each: what the article says, what's changed, and what should replace it.

## Missing Angles & Evidence
What did the research surface that the article completely ignores? Prioritise:
- Fresh data or studies published after the article
- Practitioner debates the article doesn't acknowledge
- Contrarian takes that would strengthen the argument
- Real examples that are more compelling than what's in the article

## Structural Gaps
Is the article missing a section it needs? Is a section too thin? Name the specific gap and what evidence from the Resource Bank would fill it.

## The One Change That Matters Most
Single sentence: if the writer can only do one thing to improve this article, what is it?"""


def _build_prompt(topic: str, scout_data: dict, power_words: str = "", existing_article: str = "") -> str:
    lines = []

    # Topic signals (formerly "keyword cluster") — framed as editorial signals
    related = scout_data.get("related_terms", [])
    if related:
        lines.append("## Topic Signals")
        lines.append("*What adjacent questions and angles surround this topic:*")
        for t in related[:15]:
            lines.append(f"- {t}")
        lines.append("")

    # Audience questions — framed as curiosity/tension signals
    paa = scout_data.get("people_also_ask", [])
    if paa:
        lines.append("## Audience Questions (What People Are Actually Asking)")
        lines.append("*Use these to find tensions and gaps, not FAQ targets:*")
        for q in paa:
            lines.append(f"- {q}")
        lines.append("")

    # Reddit / forums — practitioner voice
    reddit = scout_data.get("reddit_results", [])
    if reddit:
        lines.append("## Practitioner Voice — Reddit & Forums")
        lines.append("*Real opinions, frustrations, and debates:*")
        for r in reddit[:8]:
            lines.append(f'**{r["title"]}**')
            if r.get("snippet"):
                lines.append(f'  → {r["snippet"][:400]}')
            lines.append(f'  URL: {r["url"]}')
        lines.append("")

    # LinkedIn — expert takes
    linkedin = scout_data.get("linkedin_results", [])
    if linkedin:
        lines.append("## Expert Takes — LinkedIn")
        lines.append("*Practitioner opinions and thought leadership angles:*")
        for r in linkedin[:6]:
            lines.append(f'**{r["title"]}**')
            if r.get("snippet"):
                lines.append(f'  → {r["snippet"][:300]}')
        lines.append("")

    # X/Twitter — niche takes, debates
    twitter = scout_data.get("twitter_results", [])
    if twitter:
        lines.append("## Niche Takes & Debates — X / Twitter")
        lines.append("*Contrarian angles, breaking takes, practitioner friction:*")
        for r in twitter[:6]:
            lines.append(f'**{r["title"]}**')
            if r.get("snippet"):
                lines.append(f'  → {r["snippet"][:200]}')
        lines.append("")

    # News — what changed recently
    news = scout_data.get("news_results", [])
    if news:
        lines.append("## What Changed Recently — Industry News")
        lines.append("*Timeliness hooks and context shifts:*")
        for r in news[:8]:
            date = f' ({r["date"]})' if r.get("date") else ""
            lines.append(f'**{r["title"]}**{date}')
            if r.get("snippet"):
                lines.append(f'  → {r["snippet"][:300]}')
            lines.append(f'  URL: {r["url"]}')
        lines.append("")

    # Reviews — real-world friction
    reviews = scout_data.get("review_results", [])
    if reviews:
        lines.append("## Real-World Friction — User Reviews")
        lines.append("*Complaints and failures = article angles:*")
        for r in reviews[:6]:
            lines.append(f'**{r["title"]}**')
            if r.get("snippet"):
                lines.append(f'  → {r["snippet"][:300]}')
        lines.append("")

    # Forums — Quora, HackerNews, community boards
    forums = scout_data.get("forum_results", [])
    if forums:
        lines.append("## Community Discussions — Quora, HackerNews & Forums")
        lines.append("*More practitioner voice beyond Reddit:*")
        for r in forums[:4]:
            lines.append(f'**{r["title"]}**')
            if r.get("snippet"):
                lines.append(f'  → {r["snippet"][:250]}')
            lines.append(f'  URL: {r["url"]}')
        lines.append("")

    # Industry blogs & newsletters — Substack, Medium, surveys, reports
    blogs = scout_data.get("blog_results", [])
    if blogs:
        lines.append("## Industry Blogs, Newsletters & Reports")
        lines.append("*Original data, surveys, and practitioner-written analysis:*")
        for r in blogs[:6]:
            lines.append(f'**{r["title"]}**')
            if r.get("snippet"):
                lines.append(f'  → {r["snippet"][:300]}')
            lines.append(f'  URL: {r["url"]}')
        lines.append("")

    # Existing web coverage — what's already out there
    web = scout_data.get("web_results", [])
    if web:
        lines.append("## What's Already Out There (Current Coverage)")
        lines.append("*Use this to identify what's been said to death and what's missing:*")
        for r in web[:6]:
            lines.append(f'**{r["title"]}** — {r["url"]}')
            if r.get("snippet"):
                lines.append(f'  → {r["snippet"][:200]}')
        lines.append("")

    if power_words and power_words.strip():
        lines.append(f"## Title Power Words\n{power_words.strip()}\n")

    research_block = "\n".join(lines)

    parts_instruction = "Write two sections:" if not existing_article else "Write three sections:"

    article_part = _build_article_improvement_section(existing_article) if existing_article else ""

    return f"""Topic: **{topic}**

Here's the raw research. Your job is to find the argument, not fill the template.

{research_block}

---

{parts_instruction}

---

# PART 1 — RESOURCE BANK

Curated research the writer can pull from directly. **Maximum 12 items total.** No padding. Only keep what's genuinely useful — a surprising stat, a real quote with edge, a case study that proves the point, a practitioner take that adds texture.

For each item:
- The actual quote, stat, or finding (not a paraphrase)
- Source attribution
- Why it earns its place: which section it supports, what it proves

Organise by type:
**Fresh Data & Studies** — stats, surveys, and original reports worth citing (flag if older than 2023)
**What Changed Recently** — news or shifts that make this timely in 2026
**Practitioner Voice** — Reddit/forum/X quotes that capture real opinion or frustration
**Expert & Practitioner Takes** — LinkedIn, Substack, Medium, or named-expert angles with teeth
**Real Examples & Case Studies** — companies or situations that prove the argument
**Review-Based Friction** — user complaints that reveal what people actually struggle with

Flag the 3 strongest finds with ⭐. These should be the spine of the article.

**Information Gain Check:** At the end of Part 1, list 2-3 points that appear in every existing article on this topic. Label them `[STALE — skip or reframe]`. The writer should avoid these.

---

# PART 2 — EDITORIAL BRIEF

## The Thesis

One sentence. The argument this article makes. Not "X is important" — an actual claim that someone could disagree with. If you can't find a defensible thesis in the research, say so and propose the angle that comes closest.

---

## Why Now

2-3 sentences max. What shifted in the last 6-12 months that makes this worth writing in 2026 specifically? AI changes, market shifts, practitioner behavior changes, a narrative that just broke. If nothing changed, say what's been building and why it's reaching a tipping point.

---

## The Debate

What do smart people in this space actively disagree about? Name the two camps. Who holds each view? What's the actual tension — not a manufactured "some say X, others say Y" but a real fault line in the industry. Cite a specific Reddit thread, LinkedIn post, or X take if you found one.

---

## Contrarian Angle

What does everyone say about this topic that's either wrong, oversimplified, or becoming outdated? What's the move that looks wrong but is actually right (or vice versa)? This is the take that makes someone share the article.

---

## Strongest Evidence (Ranked)

Top 5 data points or examples from the Resource Bank, ranked by: freshness + surprise value + argument support. For each:
- The finding
- Why it ranks here
- Which section of the article it belongs in

Cut anything that doesn't survive the question: "Would a smart practitioner already know this?"

---

## Real Examples & Case Studies

3-5 specific companies, products, campaigns, or situations that illustrate the thesis. For each: what happened, why it matters, what it proves. Name names. If you couldn't find strong examples in the research, flag what type of example would be ideal and where to find it.

---

## Narrative Structure

This is not a bullet outline. It's the story arc.

Describe in 4-6 sentences how the article moves: where it opens, what tension it establishes, how it builds the argument, what the turn or reveal is, and how it lands. Think of it as the pitch you'd give an editor — what journey does the reader go on?

---

## Section Plan

6-8 sections with opinionated headings. Every heading = a claim or a stake, not a label.

**No:** "What is X", "Benefits of X", "How to X", "FAQs about X"
**Yes:** Headings that take a position, reveal a tension, or name a specific outcome

For each section:
**[Heading with a point of view]**
*The job of this section:* [one line — what it argues or proves]
*Open with:* [specific evidence, quote, or moment from the Resource Bank]
*The move:* [what the writer needs to do here — not what to cover, but how to argue it]

Inline callouts where they apply:
- 💬 "[specific practitioner quote from research]"
- `[CASE STUDY: company/situation]`
- `[VISUAL: describe the infographic or chart idea]`
- `[PRODUCT FIT: where/how to mention the product naturally — one line]`
- `[INFORMATION GAIN: what this section adds that existing articles miss]`

---

## Opening Options

2 strong openers. Each must lead with the argument — not a stat dump, not a definition, not "In today's world...".

**Option A — Contrarian open:** Start with the thing everyone gets wrong.
**Option B — Scene/moment open:** Drop into a specific situation that embodies the tension.

Both should make a reader think "I haven't seen it framed that way before."

---

## Title Options

3 options. Each uses the thesis, not just the keyword. Each could stand alone as a tweet that gets engagement.

**Option 1 — [angle type]:** [Title]
*What makes this land:* [one sentence]

Use power words sparingly — only where they sharpen, not decorate.

---

## Visual & Infographic Ideas

2-3 specific visual concepts that would make this article more shareable or easier to understand. Not "add an image here" — describe what the visual shows, why it helps the argument, and what format (comparison table, timeline, decision tree, annotated screenshot, etc.).

---

## Information Gain Check

Final gut-check. 3 bullets:
- What does this article say that the top 3 Google results don't?
- What angle are we deliberately not taking (and why)?
- What's the one thing a reader should remember 48 hours after reading this?

---

End with one sentence: the single editorial decision that will determine whether this article is worth reading.
{article_part}"""


def generate_brief(
    topic: str,
    scout_data: dict,
    api_key: str,
    power_words: str = "",
    existing_article: str = "",
    progress_callback=None,
) -> tuple[str | None, str | None]:
    """
    Generate a Resource Bank + Editorial Brief using Claude.
    Returns (brief_text, error).
    """
    try:
        client = Anthropic(api_key=api_key)
        prompt = _build_prompt(topic, scout_data, power_words, existing_article)

        if progress_callback:
            progress_callback("Claude is finding the thesis, the debate, and the fresh angles...")

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
