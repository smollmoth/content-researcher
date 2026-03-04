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

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Content Researcher",
    page_icon="🔬",
    layout="wide"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Base ── */
[data-testid="stAppViewContainer"] {
    background-color: #F4F4F8;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] {
    background-color: #FFFFFF;
    border-right: 1px solid #EBEBEF;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 24px; }

/* ── Typography ── */
* { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif; }

/* ── Hero ── */
.hero {
    background: linear-gradient(135deg, #5A4FCF 0%, #7B68EE 60%, #9B8FFF 100%);
    border-radius: 20px;
    padding: 44px 48px;
    color: white;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 240px; height: 240px;
    background: rgba(255,255,255,0.06);
    border-radius: 50%;
}
.hero::after {
    content: '';
    position: absolute;
    bottom: -60px; right: 80px;
    width: 160px; height: 160px;
    background: rgba(255,255,255,0.04);
    border-radius: 50%;
}
.hero-eyebrow {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.65);
    margin-bottom: 10px;
}
.hero h1 {
    font-size: 2.4rem;
    font-weight: 800;
    color: white;
    margin: 0 0 10px 0;
    line-height: 1.15;
}
.hero p {
    font-size: 1.05rem;
    color: rgba(255,255,255,0.8);
    margin: 0;
    max-width: 520px;
    line-height: 1.6;
}
.hero-pills {
    display: flex;
    gap: 10px;
    margin-top: 22px;
    flex-wrap: wrap;
}
.hero-pill {
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 20px;
    padding: 5px 14px;
    font-size: 0.78rem;
    font-weight: 600;
    color: white;
}

/* ── Cards ── */
.card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 28px 32px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04);
    border: 1px solid #EBEBEF;
    margin-bottom: 20px;
}
.card-title {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #9CA3AF;
    margin-bottom: 16px;
}
.card-heading {
    font-size: 1.1rem;
    font-weight: 700;
    color: #111827;
    margin-bottom: 4px;
}
.card-sub {
    font-size: 0.85rem;
    color: #6B7280;
    margin-bottom: 20px;
}

/* ── Metric row ── */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 24px;
}
.metric-card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 22px 20px;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    border: 1px solid #EBEBEF;
}
.metric-number {
    font-size: 2.1rem;
    font-weight: 800;
    color: #5A4FCF;
    line-height: 1;
}
.metric-label {
    font-size: 0.72rem;
    color: #9CA3AF;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    font-weight: 600;
    margin-top: 6px;
}

/* ── Gap items ── */
.gap-list { display: flex; flex-direction: column; gap: 8px; margin-top: 4px; }
.gap-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 13px 18px;
    background: #F9FAFB;
    border-radius: 10px;
    border-left: 3px solid #5A4FCF;
}
.gap-item-term { font-weight: 600; color: #111827; font-size: 0.88rem; }
.gap-item-meta { font-size: 0.75rem; color: #9CA3AF; font-weight: 500; }

.gap-item-unique {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 13px 18px;
    background: #F9FAFB;
    border-radius: 10px;
    border-left: 3px solid #F59E0B;
}

/* ── Keyword chips ── */
.chip-wrap { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.chip {
    background: #F3F4F6;
    border: 1px solid #E5E7EB;
    border-radius: 20px;
    padding: 5px 13px;
    font-size: 0.78rem;
    color: #374151;
    font-weight: 600;
    display: inline-block;
}
.chip-purple {
    background: #EDE9FE;
    border-color: #DDD6FE;
    color: #5B21B6;
}
.chip-green {
    background: #D1FAE5;
    border-color: #A7F3D0;
    color: #065F46;
}
.chip-yellow {
    background: #FEF3C7;
    border-color: #FDE68A;
    color: #92400E;
}
.chip-blue {
    background: #DBEAFE;
    border-color: #BFDBFE;
    color: #1E40AF;
}

/* ── Badges ── */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.03em;
}
.badge-success { background: #D1FAE5; color: #059669; }
.badge-error   { background: #FEE2E2; color: #DC2626; }
.badge-info    { background: #DBEAFE; color: #2563EB; }
.badge-warn    { background: #FEF3C7; color: #D97706; }

/* ── Divider ── */
.divider {
    height: 1px;
    background: #EBEBEF;
    margin: 24px 0;
}

/* ── Section label ── */
.section-label {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #9CA3AF;
    font-weight: 700;
    margin-bottom: 10px;
}

/* ── Pipeline steps in sidebar ── */
.pipeline-step {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    border-radius: 10px;
    margin-bottom: 6px;
    background: #F9FAFB;
}
.pipeline-step-icon {
    font-size: 1rem;
    width: 28px;
    text-align: center;
}
.pipeline-step-text {
    font-size: 0.82rem;
    color: #374151;
    font-weight: 500;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: white;
    border-radius: 12px;
    padding: 6px;
    gap: 4px;
    border: 1px solid #EBEBEF;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 9px 22px;
    font-weight: 600;
    font-size: 0.85rem;
    color: #6B7280;
}
.stTabs [aria-selected="true"] {
    background: #5A4FCF !important;
    color: white !important;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 12px;
    font-weight: 600;
    transition: all 0.2s;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #5A4FCF 0%, #7B68EE 100%);
    border: none;
    color: white;
    padding: 14px 28px;
    font-size: 0.95rem;
    width: 100%;
}
.stButton > button[kind="primary"]:hover { opacity: 0.9; transform: translateY(-1px); }

/* ── Download buttons ── */
.stDownloadButton > button {
    border-radius: 10px;
    font-weight: 600;
    font-size: 0.85rem;
    width: 100%;
    border: 1px solid #E5E7EB;
    color: #374151;
    background: white;
    padding: 10px 16px;
}
.stDownloadButton > button:hover {
    background: #F9FAFB;
    border-color: #5A4FCF;
    color: #5A4FCF;
}

/* ── Input fields ── */
.stTextInput > label {
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    color: #374151 !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.stTextInput > div > div > input {
    border-radius: 10px !important;
    border: 1.5px solid #E5E7EB !important;
    padding: 10px 14px !important;
    font-size: 0.9rem !important;
    transition: border-color 0.2s;
}
.stTextInput > div > div > input:focus {
    border-color: #5A4FCF !important;
    box-shadow: 0 0 0 3px rgba(90,79,207,0.1) !important;
}
.stSlider > label {
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    color: #374151 !important;
}
.stCheckbox > label {
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    color: #374151 !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
    border: 1px solid #E5E7EB !important;
    border-radius: 12px !important;
    overflow: hidden;
    margin-bottom: 10px;
}
[data-testid="stExpander"] summary {
    font-weight: 600;
    color: #374151;
}

/* ── Status boxes ── */
[data-testid="stStatusWidget"] {
    border-radius: 12px !important;
    border: 1px solid #E5E7EB !important;
}

/* ── Success / info / warning ── */
.stSuccess, .stInfo, .stWarning, .stError {
    border-radius: 12px !important;
}

/* ── Scout result cards ── */
.result-card {
    background: #F9FAFB;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 10px;
}
.result-card-title {
    font-weight: 700;
    color: #111827;
    font-size: 0.88rem;
    margin-bottom: 4px;
}
.result-card-meta {
    font-size: 0.78rem;
    color: #9CA3AF;
    line-height: 1.5;
}

/* ── Footer ── */
.footer {
    text-align: center;
    padding: 24px;
    font-size: 0.78rem;
    color: #9CA3AF;
}
.footer a { color: #5A4FCF; text-decoration: none; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-label">API Keys</div>', unsafe_allow_html=True)
    anthropic_key = st.text_input(
        "Anthropic API Key",
        type="password",
        placeholder="sk-ant-...",
        help="Get yours at console.anthropic.com"
    )
    serper_key = st.text_input(
        "Serper API Key",
        type="password",
        placeholder="your-serper-key",
        help="Get yours at serper.dev"
    )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Settings</div>', unsafe_allow_html=True)

    rate_limit = st.slider(
        "Request delay (seconds)",
        min_value=0.5,
        max_value=4.0,
        value=1.0,
        step=0.5,
        help="Pause between scraping each URL to avoid being blocked"
    )
    run_scout_search = st.checkbox(
        "Enable Scout (web + Reddit)",
        value=True,
        help="Uses Serper API to find web results, PAA questions and Reddit discussions"
    )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">How it works</div>', unsafe_allow_html=True)

    steps = [
        ("🕷️", "Extract competitor content"),
        ("🔭", "Scout web & Reddit"),
        ("🧠", "Analyse content gaps"),
        ("📋", "Generate brief with Claude"),
    ]
    for icon, text in steps:
        st.markdown(f"""
        <div class="pipeline-step">
            <span class="pipeline-step-icon">{icon}</span>
            <span class="pipeline-step-text">{text}</span>
        </div>
        """, unsafe_allow_html=True)

# ── Keys check ────────────────────────────────────────────────────────────────
keys_ok = bool(anthropic_key)
if run_scout_search and not serper_key:
    st.sidebar.warning("Add a Serper key to enable Scout, or uncheck it above.")
    keys_ok = False

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-eyebrow">AI-Powered Research</div>
    <h1>Content Researcher</h1>
    <p>Analyse competitors, uncover content gaps, and generate a strategic brief — powered by Claude.</p>
    <div class="hero-pills">
        <span class="hero-pill">🕷️ Content Extraction</span>
        <span class="hero-pill">🔭 Web & Reddit Scout</span>
        <span class="hero-pill">🧠 Gap Analysis</span>
        <span class="hero-pill">📋 AI Brief</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Topic input ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="card">
    <div class="card-title">Step 1 — Topic</div>
    <div class="card-heading">What are you writing about?</div>
    <div class="card-sub">Enter your target keyword or topic. This is used for Scout searches.</div>
</div>
""", unsafe_allow_html=True)

topic = st.text_input(
    "Target Keyword / Topic",
    placeholder="e.g. best running shoes for flat feet",
    label_visibility="collapsed"
)

# ── Competitor URLs ───────────────────────────────────────────────────────────
st.markdown("""
<div class="card" style="margin-top:8px;">
    <div class="card-title">Step 2 — Competitors</div>
    <div class="card-heading">Add up to 5 competitor URLs</div>
    <div class="card-sub">Paste the full URLs of articles you want to analyse and outperform.</div>
</div>
""", unsafe_allow_html=True)

competitor_urls = []
cols = st.columns(2)
for i in range(5):
    col = cols[i % 2]
    with col:
        url = st.text_input(
            f"Competitor {i + 1}",
            placeholder=f"https://example.com/article-{i+1}",
            key=f"url_{i}"
        )
        if url.strip():
            competitor_urls.append(url.strip())

# ── Run button ────────────────────────────────────────────────────────────────
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
can_run = bool(topic and competitor_urls and keys_ok)

col_btn, col_hint = st.columns([1, 2])
with col_btn:
    run_btn = st.button(
        "🚀 Start Research",
        type="primary",
        disabled=not can_run,
        help="Fill in topic, at least one competitor URL, and API keys to start"
    )
with col_hint:
    if not anthropic_key:
        st.markdown('<span class="badge badge-warn">👈 Add your Anthropic key in the sidebar</span>', unsafe_allow_html=True)
    elif not topic:
        st.markdown('<span class="badge badge-info">Enter a topic above to continue</span>', unsafe_allow_html=True)
    elif not competitor_urls:
        st.markdown('<span class="badge badge-info">Add at least one competitor URL</span>', unsafe_allow_html=True)
    elif can_run:
        st.markdown(f'<span class="badge badge-success">✓ Ready — {len(competitor_urls)} URL{"s" if len(competitor_urls) > 1 else ""} queued</span>', unsafe_allow_html=True)

# ── Pipeline ──────────────────────────────────────────────────────────────────
if run_btn and can_run:

    # STEP 1: Extract
    with st.status("🕷️ Extracting competitor content...", expanded=True) as status1:
        st.write(f"Scraping {len(competitor_urls)} URL{'s' if len(competitor_urls) > 1 else ''}...")

        def extract_progress(done, total, url):
            st.write(f"✅ ({done}/{total}) {url[:80]}")

        competitor_results = scrape_urls(competitor_urls, rate_limit=rate_limit, progress_callback=extract_progress)
        successful = [r for r in competitor_results if r['status'] == 'Success']
        failed     = [r for r in competitor_results if r['status'] != 'Success']
        st.write(f"**{len(successful)} successful** / {len(failed)} failed")
        for r in failed:
            st.write(f"❌ {r['url']} — {r['error']}")
        status1.update(label=f"✅ Step 1 complete — {len(successful)} pages extracted", state="complete")

    # STEP 2: Scout
    scout_data = {}
    if run_scout_search and serper_key:
        with st.status("🔭 Scouting web & Reddit...", expanded=True) as status2:
            def scout_progress(msg):
                st.write(f"→ {msg}")
            scout_data = run_scout(topic, serper_key, progress_callback=scout_progress)
            st.write(f"📰 {len(scout_data.get('web_results', []))} web results")
            st.write(f"💬 {len(scout_data.get('reddit_results', []))} Reddit threads")
            st.write(f"❓ {len(scout_data.get('people_also_ask', []))} PAA questions")
            st.write(f"🔗 {len(scout_data.get('related_searches', []))} related searches")
            status2.update(label="✅ Step 2 complete — Scout finished", state="complete")
    else:
        st.info("Scout skipped (no Serper key or disabled in settings).")

    # STEP 3: Gap Analysis
    with st.status("🧠 Analysing content gaps...", expanded=True) as status3:
        st.write("Finding common topics, unique angles and content gaps...")
        gap_analysis = analyze_competitor_content(competitor_results)
        gap_summary  = format_gap_summary(gap_analysis, scout_data if scout_data else None)
        n = gap_analysis['total_competitors_analyzed']
        st.write(f"✅ Analysed {n} competitors")
        st.write(f"✅ Found {len(gap_analysis['common_topics'])} common topics")
        st.write(f"✅ Found {len(gap_analysis['all_keywords'])} key terms")
        st.write(f"✅ Found {len(gap_analysis['unique_topics'])} unique angles")
        status3.update(label="✅ Step 3 complete — Gap analysis done", state="complete")

    # STEP 4: Claude
    with st.status("📋 Generating content brief with Claude...", expanded=True) as status4:
        competitor_titles = [r.get('title', '') for r in competitor_results if r.get('title')]

        def strategist_progress(msg):
            st.write(f"→ {msg}")

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

    # ── Results ───────────────────────────────────────────────────────────────
    if brief:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.success("🎉 Research complete! Your content brief is ready.")

        # Metrics row
        paa_count     = len(scout_data.get('people_also_ask', []))
        reddit_count  = len(scout_data.get('reddit_results', []))
        common_count  = len(gap_analysis['common_topics'])
        unique_count  = len(gap_analysis['unique_topics'])

        st.markdown(f"""
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-number">{len(successful)}</div>
                <div class="metric-label">Competitors Analysed</div>
            </div>
            <div class="metric-card">
                <div class="metric-number">{common_count}</div>
                <div class="metric-label">Common Topics</div>
            </div>
            <div class="metric-card">
                <div class="metric-number">{unique_count}</div>
                <div class="metric-label">Unique Angles</div>
            </div>
            <div class="metric-card">
                <div class="metric-number">{paa_count}</div>
                <div class="metric-label">PAA Questions</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Tabs
        tab_brief, tab_gaps, tab_scout, tab_competitors = st.tabs([
            "📋 Content Brief",
            "🧠 Gap Analysis",
            "🔭 Scout Results",
            "🏆 Competitors",
        ])

        # ── Tab: Content Brief ────────────────────────────────────────────────
        with tab_brief:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(brief)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Tab: Gap Analysis ─────────────────────────────────────────────────
        with tab_gaps:
            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown(f"""
                <div class="card">
                    <div class="card-title">Common Topics</div>
                    <div class="card-heading">All competitors cover these</div>
                    <div class="card-sub">Must-have content for your article.</div>
                    <div class="gap-list">
                """, unsafe_allow_html=True)

                if gap_analysis['common_topics']:
                    for item in gap_analysis['common_topics'][:20]:
                        st.markdown(f"""
                        <div class="gap-item">
                            <span class="gap-item-term">{item['term']}</span>
                            <span class="gap-item-meta">{item['competitor_count']}/{n} competitors · {item['total_mentions']} mentions</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No common topics found.")

                st.markdown('</div></div>', unsafe_allow_html=True)

            with col_b:
                st.markdown(f"""
                <div class="card">
                    <div class="card-title">Unique Angles</div>
                    <div class="card-heading">Only one competitor covers these</div>
                    <div class="card-sub">Differentiation opportunities for your article.</div>
                """, unsafe_allow_html=True)

                if gap_analysis['unique_topics']:
                    for url, terms in list(gap_analysis['unique_topics'].items())[:5]:
                        short_url = url.replace('https://', '').replace('http://', '')[:50]
                        chips_html = ''.join([f'<span class="chip chip-yellow">{t}</span>' for t in terms[:10]])
                        st.markdown(f"""
                        <div style="margin-bottom:16px;">
                            <div style="font-size:0.75rem;font-weight:700;color:#9CA3AF;margin-bottom:6px;">{short_url}</div>
                            <div class="chip-wrap">{chips_html}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No strongly unique angles found.")

                st.markdown('</div>', unsafe_allow_html=True)

            # Keywords
            st.markdown("""
            <div class="card">
                <div class="card-title">Top Keywords</div>
                <div class="card-heading">Most frequently mentioned terms</div>
                <div class="card-sub">Ranked by total mentions across all competitor pages.</div>
            """, unsafe_allow_html=True)

            if gap_analysis['all_keywords']:
                chips_html = ''.join([
                    f'<span class="chip chip-purple">{item["term"]} <span style="opacity:0.6;font-weight:400;">×{item["mentions"]}</span></span>'
                    for item in gap_analysis['all_keywords'][:30]
                ])
                st.markdown(f'<div class="chip-wrap">{chips_html}</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

            # Headings
            if gap_analysis.get('heading_themes'):
                st.markdown("""
                <div class="card">
                    <div class="card-title">Heading Themes</div>
                    <div class="card-heading">How competitors structure their articles</div>
                    <div class="card-sub">Common heading patterns found across competitor pages.</div>
                """, unsafe_allow_html=True)
                chips_html = ''.join([f'<span class="chip">{h}</span>' for h in gap_analysis['heading_themes'][:40]])
                st.markdown(f'<div class="chip-wrap">{chips_html}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        # ── Tab: Scout Results ────────────────────────────────────────────────
        with tab_scout:
            if scout_data:
                col1, col2 = st.columns(2)

                with col1:
                    # PAA
                    st.markdown("""
                    <div class="card">
                        <div class="card-title">People Also Ask</div>
                        <div class="card-heading">Questions from Google</div>
                        <div class="card-sub">Real questions people search for on this topic.</div>
                    """, unsafe_allow_html=True)
                    for q in scout_data.get('people_also_ask', []):
                        st.markdown(f'<div class="gap-item"><span class="gap-item-term">❓ {q}</span></div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    # Related searches
                    st.markdown("""
                    <div class="card">
                        <div class="card-title">Related Searches</div>
                        <div class="card-heading">Keyword variations</div>
                        <div class="card-sub">Related terms people search for.</div>
                    """, unsafe_allow_html=True)
                    chips_html = ''.join([f'<span class="chip chip-blue">{s}</span>' for s in scout_data.get('related_searches', [])])
                    st.markdown(f'<div class="chip-wrap">{chips_html}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                with col2:
                    # Reddit
                    st.markdown("""
                    <div class="card">
                        <div class="card-title">Reddit Discussions</div>
                        <div class="card-heading">Community conversations</div>
                        <div class="card-sub">What real people are saying about this topic.</div>
                    """, unsafe_allow_html=True)
                    for r in scout_data.get('reddit_results', []):
                        st.markdown(f"""
                        <div class="result-card">
                            <div class="result-card-title"><a href="{r['url']}" target="_blank" style="color:#5A4FCF;text-decoration:none;">{r['title']}</a></div>
                            <div class="result-card-meta">{r.get('snippet', '')[:200]}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                # Web results (full width)
                st.markdown("""
                <div class="card">
                    <div class="card-title">Web Results</div>
                    <div class="card-heading">Top search results</div>
                    <div class="card-sub">The pages currently ranking for this topic.</div>
                """, unsafe_allow_html=True)
                web_cols = st.columns(2)
                for i, r in enumerate(scout_data.get('web_results', [])[:6]):
                    with web_cols[i % 2]:
                        st.markdown(f"""
                        <div class="result-card">
                            <div class="result-card-title"><a href="{r['url']}" target="_blank" style="color:#5A4FCF;text-decoration:none;">{r['title']}</a></div>
                            <div class="result-card-meta">{r.get('snippet', '')[:180]}</div>
                        </div>
                        """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            else:
                st.info("Scout was not run. Enable it in the sidebar with a Serper API key.")

        # ── Tab: Competitors ──────────────────────────────────────────────────
        with tab_competitors:
            st.markdown("""
            <div class="card">
                <div class="card-title">Competitor Pages</div>
                <div class="card-heading">Pages analysed in this research run</div>
            </div>
            """, unsafe_allow_html=True)

            for r in competitor_results:
                status_icon = "✅" if r['status'] == 'Success' else "❌"
                with st.expander(f"{status_icon} {r['url']}"):
                    if r['status'] == 'Success':
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown(f"""
                            <div style="margin-bottom:8px;">
                                <span class="badge badge-success">✓ Success</span>
                            </div>
                            <div style="font-size:0.85rem;color:#374151;margin-bottom:6px;"><strong>Title:</strong> {r.get('title', 'N/A')}</div>
                            <div style="font-size:0.85rem;color:#374151;margin-bottom:6px;"><strong>H1:</strong> {r.get('h1', 'N/A')}</div>
                            <div style="font-size:0.85rem;color:#374151;"><strong>Content:</strong> {r.get('content_length', 0):,} characters</div>
                            """, unsafe_allow_html=True)
                        with c2:
                            if r.get('headings'):
                                st.markdown('<div style="font-size:0.82rem;font-weight:700;color:#374151;margin-bottom:8px;">Headings</div>', unsafe_allow_html=True)
                                for h in r['headings'][:15]:
                                    st.markdown(f'<div style="font-size:0.8rem;color:#6B7280;padding:3px 0;border-bottom:1px solid #F3F4F6;">— {h}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<span class="badge badge-error">✗ Failed: {r.get("error", "Unknown error")}</span>', unsafe_allow_html=True)

        # ── Downloads ─────────────────────────────────────────────────────────
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="card">
            <div class="card-title">Export</div>
            <div class="card-heading">Download your research</div>
            <div class="card-sub">Save the results in your preferred format.</div>
        </div>
        """, unsafe_allow_html=True)

        dl1, dl2, dl3 = st.columns(3)
        slug = topic[:30].replace(' ', '_')

        with dl1:
            st.download_button(
                label="📋 Content Brief (.md)",
                data=brief,
                file_name=f"content_brief_{slug}.md",
                mime="text/markdown"
            )

        with dl2:
            full_report = f"""# Content Research Report\n\n**Topic:** {topic}\n**Competitors Analysed:** {len(competitor_urls)}\n\n---\n\n{brief}\n\n---\n\n## Raw Gap Analysis\n\n{gap_summary}\n"""
            st.download_button(
                label="📄 Full Report (.md)",
                data=full_report,
                file_name=f"research_report_{slug}.md",
                mime="text/markdown"
            )

        with dl3:
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
                label="🗂️ JSON Data (.json)",
                data=json.dumps(export_data, indent=2),
                file_name=f"research_data_{slug}.json",
                mime="application/json"
            )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    Powered by <a href="https://anthropic.com">Claude (Anthropic)</a> · <a href="https://serper.dev">Serper.dev</a> · BeautifulSoup
</div>
""", unsafe_allow_html=True)
