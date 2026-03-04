"""
Content Researcher
A unified tool that researches competitor content, finds gaps,
scouts the web and Reddit, then generates a strategic content brief using Claude.

Pipeline:
  1. Content Extractor  — scrapes competitor URLs (BeautifulSoup)
  2. Scout              — searches web + Reddit (Serper API)
  3. Gap Finder         — analyses what competitors cover and miss
  4. Claude Strategist  — generates a full content brief

Author: Built with Lee Foot's toolkit
"""
import streamlit as st
from io import BytesIO
import json

from modules.extractor import scrape_urls
from modules.scout import run_scout
from modules.gap_finder import analyze_competitor_content, format_gap_summary
from modules.strategist import generate_brief

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Content Researcher",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 Content Researcher")
st.markdown("*Research competitors, find content gaps, and generate a strategic content brief — powered by Claude.*")

# ── Sidebar — API Keys ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔑 API Keys")
    anthropic_key = st.text_input(
        "Anthropic API Key",
        type="password",
        help="Get from console.anthropic.com"
    )
    serper_key = st.text_input(
        "Serper API Key",
        type="password",
        help="Get from serper.dev"
    )

    st.divider()
    st.header("⚙️ Settings")
    rate_limit = st.slider(
        "Delay between requests (s)",
        min_value=0.5,
        max_value=4.0,
        value=1.0,
        step=0.5,
        help="Pause between scraping each URL to avoid being blocked"
    )
    run_scout_search = st.checkbox(
        "Run Scout (web + Reddit search)",
        value=True,
        help="Uses Serper API to find web results, PAA questions and Reddit discussions"
    )

    st.divider()
    st.markdown("**Pipeline:**")
    st.markdown("1. 🕷️ Extract competitor content")
    st.markdown("2. 🔭 Scout web & Reddit")
    st.markdown("3. 🧠 Analyse gaps")
    st.markdown("4. 📋 Generate content brief")

# ── Keys check ───────────────────────────────────────────────────────────────
keys_ok = bool(anthropic_key)
if run_scout_search and not serper_key:
    st.sidebar.warning("Serper key needed for Scout. Uncheck Scout or add key.")
    keys_ok = False

# ── Main inputs ───────────────────────────────────────────────────────────────
st.subheader("📝 Research Brief Input")

col1, col2 = st.columns([2, 1])
with col1:
    topic = st.text_input(
        "Topic / Target Keyword",
        placeholder="e.g. best running shoes for flat feet",
        help="The topic you want to write about. Used for Scout searches."
    )

with col2:
    st.markdown("&nbsp;", unsafe_allow_html=True)
    st.info("Enter your topic and up to 5 competitor URLs below.")

st.subheader("🏆 Competitor URLs")
st.markdown("Enter up to 5 competitor URLs you want to analyse.")

competitor_urls = []
cols = st.columns(2)
for i in range(5):
    col = cols[i % 2]
    with col:
        url = st.text_input(
            f"Competitor {i + 1}",
            placeholder=f"https://competitor{i+1}.com/article",
            key=f"url_{i}"
        )
        if url.strip():
            competitor_urls.append(url.strip())

# ── Run button ────────────────────────────────────────────────────────────────
st.divider()
can_run = bool(topic and competitor_urls and keys_ok)
run_btn = st.button(
    "🚀 Start Research",
    type="primary",
    disabled=not can_run,
    help="Fill in topic, at least one competitor URL, and API keys to start"
)

if not can_run and not run_btn:
    if not anthropic_key:
        st.info("👈 Add your Anthropic API key in the sidebar to get started.")
    elif not topic:
        st.info("Enter a topic above.")
    elif not competitor_urls:
        st.info("Enter at least one competitor URL.")

# ── Pipeline execution ────────────────────────────────────────────────────────
if run_btn and can_run:
    # ── STEP 1: Extract ──────────────────────────────────────────────────────
    with st.status("🕷️ Step 1: Extracting competitor content...", expanded=True) as status1:
        st.write(f"Scraping {len(competitor_urls)} URLs...")

        def extract_progress(done, total, url):
            st.write(f"  ✅ ({done}/{total}) {url[:70]}")

        competitor_results = scrape_urls(competitor_urls, rate_limit=rate_limit, progress_callback=extract_progress)

        successful = [r for r in competitor_results if r['status'] == 'Success']
        failed = [r for r in competitor_results if r['status'] != 'Success']

        st.write(f"**{len(successful)} successful** / {len(failed)} failed")
        if failed:
            for r in failed:
                st.write(f"  ❌ {r['url']} — {r['error']}")

        status1.update(label=f"✅ Step 1 complete — {len(successful)} pages extracted", state="complete")

    # ── STEP 2: Scout ────────────────────────────────────────────────────────
    scout_data = {}
    if run_scout_search and serper_key:
        with st.status("🔭 Step 2: Scouting web & Reddit...", expanded=True) as status2:
            def scout_progress(msg):
                st.write(f"  → {msg}")

            scout_data = run_scout(topic, serper_key, progress_callback=scout_progress)

            st.write(f"  📰 {len(scout_data.get('web_results', []))} web results")
            st.write(f"  💬 {len(scout_data.get('reddit_results', []))} Reddit threads")
            st.write(f"  ❓ {len(scout_data.get('people_also_ask', []))} PAA questions")
            st.write(f"  🔗 {len(scout_data.get('related_searches', []))} related searches")

            status2.update(label="✅ Step 2 complete — Scout finished", state="complete")
    else:
        st.info("Scout skipped (no Serper key or disabled in settings).")

    # ── STEP 3: Gap Analysis ─────────────────────────────────────────────────
    with st.status("🧠 Step 3: Analysing content gaps...", expanded=True) as status3:
        st.write("Finding common topics, unique angles, and content gaps...")

        gap_analysis = analyze_competitor_content(competitor_results)
        gap_summary = format_gap_summary(gap_analysis, scout_data if scout_data else None)

        n = gap_analysis['total_competitors_analyzed']
        st.write(f"  ✅ Analysed {n} competitors")
        st.write(f"  ✅ Found {len(gap_analysis['common_topics'])} common topics")
        st.write(f"  ✅ Found {len(gap_analysis['all_keywords'])} key terms")
        st.write(f"  ✅ Found {len(gap_analysis['unique_topics'])} unique angles")

        status3.update(label="✅ Step 3 complete — Gap analysis done", state="complete")

    # ── STEP 4: Claude Strategist ────────────────────────────────────────────
    with st.status("📋 Step 4: Generating content brief with Claude...", expanded=True) as status4:
        competitor_titles = [r.get('title', '') for r in competitor_results if r.get('title')]

        def strategist_progress(msg):
            st.write(f"  → {msg}")

        brief, error = generate_brief(
            topic=topic,
            gap_summary=gap_summary,
            competitor_titles=competitor_titles,
            api_key=anthropic_key,
            progress_callback=strategist_progress
        )

        if error:
            st.error(f"Claude failed: {error}")
            status4.update(label="❌ Step 4 failed", state="error")
        else:
            status4.update(label="✅ Step 4 complete — Content brief ready", state="complete")

    # ── Results ──────────────────────────────────────────────────────────────
    if brief:
        st.divider()
        st.success("🎉 Research complete! Your content brief is ready.")

        # Tabs for different views
        tab_brief, tab_gaps, tab_scout, tab_competitors = st.tabs([
            "📋 Content Brief",
            "🧠 Gap Analysis",
            "🔭 Scout Results",
            "🏆 Competitor Overview"
        ])

        with tab_brief:
            st.markdown(brief)

        with tab_gaps:
            st.subheader("Common Topics (Competitors All Cover These)")
            if gap_analysis['common_topics']:
                for item in gap_analysis['common_topics'][:20]:
                    st.markdown(f"- **{item['term']}** — {item['competitor_count']}/{n} competitors, {item['total_mentions']} mentions")
            else:
                st.info("No common topics found.")

            st.subheader("Top Keywords")
            if gap_analysis['all_keywords']:
                for item in gap_analysis['all_keywords'][:20]:
                    st.markdown(f"- `{item['term']}` — {item['mentions']} mentions across {item['competitor_coverage']} competitors")

            st.subheader("Unique Angles (Only One Competitor Covers)")
            if gap_analysis['unique_topics']:
                for url, terms in gap_analysis['unique_topics'].items():
                    st.markdown(f"**{url}**")
                    st.markdown(", ".join(terms[:15]))
            else:
                st.info("No strongly unique angles found.")

            st.subheader("Competitor Heading Structure")
            if gap_analysis['heading_themes']:
                for h in gap_analysis['heading_themes']:
                    st.markdown(f"- {h}")

        with tab_scout:
            if scout_data:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("❓ People Also Ask")
                    for q in scout_data.get('people_also_ask', []):
                        st.markdown(f"- {q}")

                    st.subheader("🔗 Related Searches")
                    for s in scout_data.get('related_searches', []):
                        st.markdown(f"- {s}")

                with col2:
                    st.subheader("💬 Reddit Discussions")
                    for r in scout_data.get('reddit_results', []):
                        st.markdown(f"**[{r['title']}]({r['url']})**")
                        if r.get('snippet'):
                            st.caption(r['snippet'][:200])
                        st.divider()

                    st.subheader("🌐 Web Results")
                    for r in scout_data.get('web_results', [])[:5]:
                        st.markdown(f"**[{r['title']}]({r['url']})**")
                        if r.get('snippet'):
                            st.caption(r['snippet'][:200])
                        st.divider()
            else:
                st.info("Scout was not run. Enable it in the sidebar with a Serper API key.")

        with tab_competitors:
            st.subheader("Competitor Pages Analysed")
            for r in competitor_results:
                status_icon = "✅" if r['status'] == 'Success' else "❌"
                with st.expander(f"{status_icon} {r['url']}"):
                    if r['status'] == 'Success':
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Title:** {r.get('title', 'N/A')}")
                            st.markdown(f"**H1:** {r.get('h1', 'N/A')}")
                            st.markdown(f"**Content length:** {r.get('content_length', 0):,} chars")
                        with col2:
                            if r.get('headings'):
                                st.markdown("**Headings:**")
                                for h in r['headings']:
                                    st.markdown(f"- {h}")
                    else:
                        st.error(f"Failed: {r.get('error', 'Unknown error')}")

        # ── Downloads ────────────────────────────────────────────────────────
        st.divider()
        st.subheader("📥 Download Results")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.download_button(
                label="📋 Download Brief (Markdown)",
                data=brief,
                file_name=f"content_brief_{topic[:30].replace(' ', '_')}.md",
                mime="text/markdown"
            )

        with col2:
            full_report = f"""# Content Research Report

**Topic:** {topic}
**Competitors Analysed:** {len(competitor_urls)}

---

{brief}

---

## Raw Gap Analysis

{gap_summary}
"""
            st.download_button(
                label="📄 Download Full Report",
                data=full_report,
                file_name=f"research_report_{topic[:30].replace(' ', '_')}.md",
                mime="text/markdown"
            )

        with col3:
            export_data = {
                'topic': topic,
                'competitor_urls': competitor_urls,
                'gap_analysis': {
                    'total_competitors': gap_analysis['total_competitors_analyzed'],
                    'common_topics': gap_analysis['common_topics'][:20],
                    'all_keywords': gap_analysis['all_keywords'][:20],
                },
                'scout': {
                    'people_also_ask': scout_data.get('people_also_ask', []),
                    'related_searches': scout_data.get('related_searches', []),
                    'reddit_count': len(scout_data.get('reddit_results', []))
                } if scout_data else {},
                'brief': brief
            }
            st.download_button(
                label="🗂️ Download JSON Data",
                data=json.dumps(export_data, indent=2),
                file_name=f"research_data_{topic[:30].replace(' ', '_')}.json",
                mime="application/json"
            )

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<small>Powered by Claude (Anthropic) · Serper.dev · BeautifulSoup</small>",
    unsafe_allow_html=True
)
