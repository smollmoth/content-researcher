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

# ── Load keys from secrets (if configured) ────────────────────────────────────
_secret_anthropic = st.secrets.get("ANTHROPIC_API_KEY", "")
_secret_serper    = st.secrets.get("SERPER_API_KEY", "")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Content Researcher",
    page_icon="🔬",
    layout="wide"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main, section[data-testid="stSidebar"] ~ div {
    background-color: #FAFAFA !important;
    color: #1A1A2E !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

[data-testid="stHeader"] {
    background: rgba(250,250,252,0.95) !important;
    border-bottom: 1px solid #E2E2EC !important;
    backdrop-filter: blur(12px);
}
[data-testid="stDecoration"] { display: none; }
[data-testid="stMainMenu"] button { color: #9999B8 !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #F5F5FA !important;
    border-right: 1px solid #E2E2EC !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 28px; }

/* ── Hero ── */
.hero {
    background: linear-gradient(135deg, #EEE9FF 0%, #E6E0FF 60%, #E2DAFF 100%);
    border-radius: 20px;
    padding: 52px 56px;
    color: #1A1A2E;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
    border: 1px solid #D0C8FF;
}
.hero::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 320px; height: 320px;
    background: radial-gradient(circle, rgba(124,110,232,0.12) 0%, transparent 70%);
    border-radius: 50%;
}
.hero::after {
    content: '';
    position: absolute;
    bottom: -80px; right: 120px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(163,148,255,0.08) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-eyebrow {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #7C6EE8;
    margin-bottom: 14px;
}
.hero h1 {
    font-size: 2.8rem;
    font-weight: 900;
    color: #1A1A2E;
    margin: 0 0 12px 0;
    line-height: 1.1;
    letter-spacing: -0.02em;
}
.hero p {
    font-size: 1.05rem;
    color: rgba(26,26,46,0.6);
    margin: 0;
    max-width: 540px;
    line-height: 1.65;
}
.hero-pills {
    display: flex;
    gap: 10px;
    margin-top: 28px;
    flex-wrap: wrap;
}
.hero-pill {
    background: rgba(124,110,232,0.12);
    border: 1px solid rgba(124,110,232,0.28);
    border-radius: 20px;
    padding: 6px 16px;
    font-size: 0.75rem;
    font-weight: 600;
    color: #6B5ED6;
}

/* ── Cards ── */
.card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 28px 32px;
    border: 1px solid #E2E2EC;
    margin-bottom: 20px;
}
.card-title {
    font-size: 0.63rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #AAAACC;
    margin-bottom: 8px;
}
.card-heading {
    font-size: 1.05rem;
    font-weight: 700;
    color: #1A1A2E;
    margin-bottom: 4px;
    letter-spacing: -0.01em;
}
.card-sub {
    font-size: 0.83rem;
    color: #7777A0;
    margin-bottom: 20px;
    line-height: 1.55;
}

/* ── Metric row ── */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 28px;
}
.metric-card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 28px 24px;
    text-align: center;
    border: 1px solid #E2E2EC;
}
.metric-number {
    font-size: 2.4rem;
    font-weight: 900;
    color: #7C6EE8;
    line-height: 1;
    letter-spacing: -0.03em;
}
.metric-label {
    font-size: 0.68rem;
    color: #AAAACC;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 700;
    margin-top: 8px;
}

/* ── Gap items ── */
.gap-list { display: flex; flex-direction: column; gap: 8px; margin-top: 4px; }
.gap-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    background: #F7F7FC;
    border-radius: 10px;
    border-left: 3px solid #7C6EE8;
    border-top: 1px solid #E2E2EC;
    border-right: 1px solid #E2E2EC;
    border-bottom: 1px solid #E2E2EC;
}
.gap-item-term { font-weight: 600; color: #1A1A2E; font-size: 0.85rem; }
.gap-item-meta { font-size: 0.72rem; color: #AAAACC; font-weight: 500; }

.gap-item-unique {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    background: #F7F7FC;
    border-radius: 10px;
    border-left: 3px solid #F59E0B;
    border-top: 1px solid #E2E2EC;
    border-right: 1px solid #E2E2EC;
    border-bottom: 1px solid #E2E2EC;
}

/* ── Keyword chips ── */
.chip-wrap { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.chip {
    background: #F0F0FA;
    border: 1px solid #E2E2F0;
    border-radius: 20px;
    padding: 5px 14px;
    font-size: 0.75rem;
    color: #666688;
    font-weight: 600;
    display: inline-block;
}
.chip-purple {
    background: rgba(124,110,232,0.08);
    border-color: rgba(124,110,232,0.2);
    color: #6B5ED6;
}
.chip-green {
    background: rgba(34,197,94,0.08);
    border-color: rgba(34,197,94,0.2);
    color: #16A34A;
}
.chip-yellow {
    background: rgba(245,158,11,0.08);
    border-color: rgba(245,158,11,0.2);
    color: #D97706;
}
.chip-blue {
    background: rgba(59,130,246,0.08);
    border-color: rgba(59,130,246,0.2);
    color: #2563EB;
}

/* ── Badges ── */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 5px 13px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.03em;
}
.badge-success { background: rgba(34,197,94,0.1);  color: #16A34A; border: 1px solid rgba(34,197,94,0.2); }
.badge-error   { background: rgba(239,68,68,0.1);  color: #DC2626; border: 1px solid rgba(239,68,68,0.2); }
.badge-info    { background: rgba(59,130,246,0.1); color: #2563EB; border: 1px solid rgba(59,130,246,0.2); }
.badge-warn    { background: rgba(245,158,11,0.1); color: #D97706; border: 1px solid rgba(245,158,11,0.2); }

/* ── Divider ── */
.divider { height: 1px; background: #E2E2EC; margin: 28px 0; }

/* ── Section label ── */
.section-label {
    font-size: 0.63rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #AAAACC;
    font-weight: 700;
    margin-bottom: 12px;
}

/* ── Pipeline steps in sidebar ── */
.pipeline-step {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    border-radius: 10px;
    margin-bottom: 6px;
    background: #FFFFFF;
    border: 1px solid #E2E2EC;
}
.pipeline-step-icon { font-size: 1rem; width: 28px; text-align: center; }
.pipeline-step-text { font-size: 0.82rem; color: #7777A0; font-weight: 500; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #F0F0FA;
    border-radius: 12px;
    padding: 5px;
    gap: 4px;
    border: 1px solid #E2E2EC;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 9px 22px;
    font-weight: 600;
    font-size: 0.83rem;
    color: #7777A0 !important;
    background: transparent !important;
}
.stTabs [aria-selected="true"] {
    background: #7C6EE8 !important;
    color: white !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 20px;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 12px;
    font-weight: 600;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.2s;
    border: 1px solid #E2E2EC !important;
    background: #F7F7FC !important;
    color: #7777A0 !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6B5ED6 0%, #8B7AEE 100%) !important;
    border: none !important;
    color: white !important;
    padding: 14px 28px;
    font-size: 0.92rem;
    width: 100%;
    box-shadow: 0 4px 20px rgba(107,94,214,0.25);
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 28px rgba(107,94,214,0.38);
}
.stButton > button:disabled {
    opacity: 0.35 !important;
    cursor: not-allowed !important;
}

/* ── Download buttons ── */
.stDownloadButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.83rem !important;
    width: 100% !important;
    border: 1px solid #E2E2EC !important;
    color: #7777A0 !important;
    background: #FAFAFA !important;
    padding: 10px 16px !important;
    font-family: 'Inter', sans-serif !important;
}
.stDownloadButton > button:hover {
    background: #F0EEFF !important;
    border-color: #7C6EE8 !important;
    color: #6B5ED6 !important;
}

/* ── Input fields ── */
.stTextInput > label {
    font-weight: 600 !important;
    font-size: 0.72rem !important;
    color: #9999B8 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextInput > div > div > input {
    border-radius: 10px !important;
    border: 1.5px solid #E2E2EC !important;
    padding: 11px 15px !important;
    font-size: 0.88rem !important;
    background: #FAFAFA !important;
    color: #1A1A2E !important;
    font-family: 'Inter', sans-serif !important;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.stTextInput > div > div > input::placeholder { color: #C8C8DC !important; }
.stTextInput > div > div > input:focus {
    border-color: #7C6EE8 !important;
    box-shadow: 0 0 0 3px rgba(124,110,232,0.12) !important;
    outline: none !important;
}
.stSlider > label {
    font-weight: 600 !important;
    font-size: 0.72rem !important;
    color: #9999B8 !important;
    font-family: 'Inter', sans-serif !important;
}
.stCheckbox > label {
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    color: #7777A0 !important;
    font-family: 'Inter', sans-serif !important;
}
.stCheckbox > label > span { color: #7777A0 !important; }

/* ── Sliders ── */
[data-testid="stSlider"] > div > div > div { background: #7C6EE8 !important; }

/* ── Expanders ── */
[data-testid="stExpander"] {
    border: 1px solid #E2E2EC !important;
    border-radius: 12px !important;
    overflow: hidden;
    margin-bottom: 10px;
    background: #FFFFFF !important;
}
[data-testid="stExpander"] summary {
    font-weight: 600;
    color: #555570 !important;
    background: #FFFFFF !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stExpander"] > div { background: #FFFFFF !important; }

/* ── Status boxes ── */
[data-testid="stStatusWidget"] {
    border-radius: 12px !important;
    border: 1px solid #E2E2EC !important;
    background: #FFFFFF !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Alert boxes ── */
.stSuccess, .stInfo, .stWarning, .stError {
    border-radius: 12px !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stMarkdownContainer"] p { color: #55556A; }

/* ── Scout result cards ── */
.result-card {
    background: #F7F7FC;
    border: 1px solid #E2E2EC;
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 10px;
}
.result-card-title {
    font-weight: 700;
    color: #1A1A2E;
    font-size: 0.85rem;
    margin-bottom: 5px;
}
.result-card-meta {
    font-size: 0.77rem;
    color: #7777A0;
    line-height: 1.55;
}

/* ── Footer ── */
.footer {
    text-align: center;
    padding: 32px;
    font-size: 0.75rem;
    color: #AAAACC;
}
.footer a { color: #7C6EE8; text-decoration: none; }
.footer a:hover { color: #6B5ED6; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #F5F5FA; }
::-webkit-scrollbar-thumb { background: #D0D0E0; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #B8B8CC; }
</style>
""", unsafe_allow_html=True)

# ── Session state for progress tracking ───────────────────────────────────────
if 'pipeline_step' not in st.session_state:
    st.session_state.pipeline_step = 0

_PIPELINE_STEPS = [("🕷️", "Extract"), ("🔭", "Scout"), ("🧠", "Analyse"), ("📋", "Brief")]

def render_progress(placeholder, current_step: int):
    """Update the pipeline progress bar using native Streamlit components."""
    with placeholder.container():
        pct = min(current_step, 4) / 4
        st.progress(pct)
        cols = st.columns(4)
        for i, (col, (icon, label)) in enumerate(zip(cols, _PIPELINE_STEPS)):
            n = i + 1
            with col:
                if n < current_step:
                    dot_bg, text_col, dot_text = "#22C55E", "#22C55E", "✓"
                elif n == current_step:
                    dot_bg, text_col, dot_text = "#7C6EE8", "#A394FF", str(n)
                else:
                    dot_bg, text_col, dot_text = "#E2E2EC", "#AAAACC", str(n)
                dot_text_color = "white" if dot_bg != "#E2E2EC" else "#AAAACC"
                st.markdown(
                    f'<div style="text-align:center;padding:4px 0 8px;">'
                    f'<div style="width:26px;height:26px;border-radius:50%;background:{dot_bg};'
                    f'color:{dot_text_color};display:inline-flex;align-items:center;justify-content:center;'
                    f'font-size:0.72rem;font-weight:800;margin-bottom:4px;">{dot_text}</div>'
                    f'<div style="font-size:0.7rem;font-weight:600;color:{text_col};">{icon} {label}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

# ── Progress bar placeholder (updates live during pipeline) ───────────────────
progress_placeholder = st.empty()
render_progress(progress_placeholder, st.session_state.pipeline_step)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-label">API Keys</div>', unsafe_allow_html=True)

    if _secret_anthropic:
        anthropic_key = _secret_anthropic
        st.markdown('<span class="badge badge-success">✓ Anthropic key configured</span>', unsafe_allow_html=True)
    else:
        anthropic_key = st.text_input(
            "Anthropic API Key",
            type="password",
            placeholder="sk-ant-...",
            help="Get yours at console.anthropic.com"
        )

    if _secret_serper:
        serper_key = _secret_serper
        st.markdown('<span class="badge badge-success">✓ Serper key configured</span>', unsafe_allow_html=True)
    else:
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

    steps_info = [
        ("🕷️", "Extract competitor content"),
        ("🔭", "Scout web & Reddit"),
        ("🧠", "Analyse content gaps"),
        ("📋", "Generate brief with Claude"),
    ]
    for icon, text in steps_info:
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

# ── Spacer below sticky bar ───────────────────────────────────────────────────
st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)

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
        "🚀  Start Research",
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
    st.session_state.pipeline_step = 1
    render_progress(progress_placeholder, 1)

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
    st.session_state.pipeline_step = 2
    render_progress(progress_placeholder, 2)

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
    st.session_state.pipeline_step = 3
    render_progress(progress_placeholder, 3)

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
    st.session_state.pipeline_step = 4
    render_progress(progress_placeholder, 4)

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

    # Mark all done
    st.session_state.pipeline_step = 5
    render_progress(progress_placeholder, 5)

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
            "📋  Content Brief",
            "🧠  Gap Analysis",
            "🔭  Scout Results",
            "🏆  Competitors",
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
                            <span class="gap-item-meta">{item['competitor_count']}/{n} · {item['total_mentions']}×</span>
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
                        <div style="margin-bottom:18px;">
                            <div style="font-size:0.7rem;font-weight:700;color:#AAAACC;margin-bottom:8px;letter-spacing:0.05em;">{short_url}</div>
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
                    f'<span class="chip chip-purple">{item["term"]} <span style="opacity:0.5;font-weight:500;">×{item["mentions"]}</span></span>'
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
                    st.markdown("""
                    <div class="card">
                        <div class="card-title">People Also Ask</div>
                        <div class="card-heading">Questions from Google</div>
                        <div class="card-sub">Real questions people search for on this topic.</div>
                    """, unsafe_allow_html=True)
                    for q in scout_data.get('people_also_ask', []):
                        st.markdown(f'<div class="gap-item"><span class="gap-item-term">❓ {q}</span></div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

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
                    st.markdown("""
                    <div class="card">
                        <div class="card-title">Reddit Discussions</div>
                        <div class="card-heading">Community conversations</div>
                        <div class="card-sub">What real people are saying about this topic.</div>
                    """, unsafe_allow_html=True)
                    for r in scout_data.get('reddit_results', []):
                        st.markdown(f"""
                        <div class="result-card">
                            <div class="result-card-title"><a href="{r['url']}" target="_blank" style="color:#7C6EE8;text-decoration:none;">{r['title']}</a></div>
                            <div class="result-card-meta">{r.get('snippet', '')[:200]}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

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
                            <div class="result-card-title"><a href="{r['url']}" target="_blank" style="color:#7C6EE8;text-decoration:none;">{r['title']}</a></div>
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
                            <div style="margin-bottom:10px;">
                                <span class="badge badge-success">✓ Success</span>
                            </div>
                            <div style="font-size:0.83rem;color:#55556A;margin-bottom:8px;"><strong style="color:#1A1A2E;">Title:</strong> {r.get('title', 'N/A')}</div>
                            <div style="font-size:0.83rem;color:#55556A;margin-bottom:8px;"><strong style="color:#1A1A2E;">H1:</strong> {r.get('h1', 'N/A')}</div>
                            <div style="font-size:0.83rem;color:#55556A;"><strong style="color:#1A1A2E;">Content:</strong> {r.get('content_length', 0):,} characters</div>
                            """, unsafe_allow_html=True)
                        with c2:
                            if r.get('headings'):
                                st.markdown('<div style="font-size:0.75rem;font-weight:700;color:#AAAACC;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">Headings</div>', unsafe_allow_html=True)
                                for h in r['headings'][:15]:
                                    st.markdown(f'<div style="font-size:0.78rem;color:#7777A0;padding:4px 0;border-bottom:1px solid #E2E2EC;">— {h}</div>', unsafe_allow_html=True)
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
