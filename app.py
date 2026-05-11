"""
Editorial Research Strategist
Topic-driven research tool: surfaces debates, practitioner opinions, and fresh
angles across Reddit, LinkedIn, news, reviews, and forums — then Claude builds
a thesis-first editorial brief.

Pipeline:
  1. Scout  — searches web, Reddit, LinkedIn, news, G2/Capterra, Twitter, forums
  2. Brief  — Claude builds curated Resource Bank + Editorial Brief from findings
"""
import streamlit as st
import json

from modules.scout import run_scout
from modules.strategist import generate_brief

# ── Load keys from secrets ─────────────────────────────────────────────────────
_secret_anthropic = st.secrets.get("ANTHROPIC_API_KEY", "")
_secret_serper    = st.secrets.get("SERPER_API_KEY", "")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Editorial Strategist",
    page_icon="✍️",
    layout="wide"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

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

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #F5F5FA !important;
    border-right: 1px solid #E2E2EC !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 28px; }

/* Hero */
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
    max-width: 580px;
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

/* Cards */
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

/* Metric row */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 16px;
    margin-bottom: 28px;
}
.metric-card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 24px 20px;
    text-align: center;
    border: 1px solid #E2E2EC;
}
.metric-number {
    font-size: 2.2rem;
    font-weight: 900;
    color: #7C6EE8;
    line-height: 1;
    letter-spacing: -0.03em;
}
.metric-label {
    font-size: 0.65rem;
    color: #AAAACC;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 700;
    margin-top: 8px;
}

/* Result cards */
.result-card {
    background: #F7F7FC;
    border: 1px solid #E2E2EC;
    border-radius: 12px;
    padding: 14px 18px;
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
.result-card-date {
    font-size: 0.7rem;
    color: #AAAACC;
    margin-top: 4px;
}

/* Keyword chips */
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
.chip-blue {
    background: rgba(59,130,246,0.08);
    border-color: rgba(59,130,246,0.2);
    color: #2563EB;
}
.chip-orange {
    background: rgba(249,115,22,0.08);
    border-color: rgba(249,115,22,0.2);
    color: #EA580C;
}

/* Badges */
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

/* Divider */
.divider { height: 1px; background: #E2E2EC; margin: 28px 0; }

/* Section label */
.section-label {
    font-size: 0.63rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #AAAACC;
    font-weight: 700;
    margin-bottom: 12px;
}

/* Pipeline steps in sidebar */
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

/* Tabs */
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
.stTabs [data-baseweb="tab-panel"] { padding-top: 20px; }

/* Buttons */
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
.stButton > button:disabled { opacity: 0.35 !important; cursor: not-allowed !important; }

/* Download buttons */
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

/* Input fields */
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
.stCheckbox > label {
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    color: #7777A0 !important;
    font-family: 'Inter', sans-serif !important;
}

/* Expanders */
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

/* Alert boxes */
.stSuccess, .stInfo, .stWarning, .stError { border-radius: 12px !important; }
[data-testid="stMarkdownContainer"] p { color: #55556A; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #F5F5FA; }
::-webkit-scrollbar-thumb { background: #D0D0E0; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #B8B8CC; }

/* Footer */
.footer {
    text-align: center;
    padding: 32px;
    font-size: 0.75rem;
    color: #AAAACC;
}
.footer a { color: #7C6EE8; text-decoration: none; }
.footer a:hover { color: #6B5ED6; }
</style>
""", unsafe_allow_html=True)

# ── Pipeline steps ─────────────────────────────────────────────────────────────
_PIPELINE_STEPS = [("🔍", "Research"), ("📋", "Brief")]

if 'pipeline_step' not in st.session_state:
    st.session_state.pipeline_step = 0


def render_progress(placeholder, current_step: int):
    with placeholder.container():
        pct = min(current_step, 2) / 2
        st.progress(pct)
        cols = st.columns(2)
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
    st.markdown('<div class="section-label">Title Power Words</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:0.78rem;color:#9999B8;margin-bottom:8px;">Claude uses these sparingly when writing title options.</div>',
        unsafe_allow_html=True
    )
    _DEFAULT_POWER_WORDS = (
        "New, Free, Discover, Secret, Powerful, Top, Best, Latest, Bonus, Ultimate, "
        "How to, Must-have, Popular, Transform, "
        "Quick, Fast, Instantly, Today, Easy, Simple, Step-by-step, Effortless, "
        "Cheat sheet, Blueprint, Roadmap, Steps, "
        "Rare, Premium, Exclusive, Unique, "
        "Proven, Research, Results, Scientifically proven, Tested, Expert, "
        "Hidden, Revealed, Insider, Little-known, Shocking"
    )
    power_words = st.text_area(
        "Power words",
        value=_DEFAULT_POWER_WORDS,
        height=120,
        label_visibility="collapsed",
    )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">How it works</div>', unsafe_allow_html=True)
    for icon, text in [
        ("🔍", "Surface debates, tensions & fresh angles"),
        ("💬", "Find practitioner opinions & case studies"),
        ("📰", "Identify what changed recently"),
        ("✍️", "Claude builds thesis-first editorial brief"),
    ]:
        st.markdown(f"""
        <div class="pipeline-step">
            <span class="pipeline-step-icon">{icon}</span>
            <span class="pipeline-step-text">{text}</span>
        </div>
        """, unsafe_allow_html=True)

# ── Key validation ────────────────────────────────────────────────────────────
keys_ok = bool(anthropic_key and serper_key)
if not serper_key:
    st.sidebar.warning("Add a Serper API key to enable research.")
if not anthropic_key:
    st.sidebar.warning("Add an Anthropic API key to generate the brief.")

# ── Spacer ────────────────────────────────────────────────────────────────────
st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-eyebrow">Editorial Research Strategist</div>
    <h1>Find the argument.<br>Write the article.</h1>
    <p>Enter a topic. We'll surface the debates, practitioner takes, and fresh angles across Reddit, LinkedIn, news, and forums — then Claude builds a thesis-first editorial brief.</p>
    <div class="hero-pills">
        <span class="hero-pill">✍️ Thesis Generation</span>
        <span class="hero-pill">💬 Practitioner Voice</span>
        <span class="hero-pill">⚡ Industry Debates</span>
        <span class="hero-pill">📰 What Changed Recently</span>
        <span class="hero-pill">📋 Editorial Brief</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Keyword input ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="card">
    <div class="card-title">Your Topic</div>
    <div class="card-heading">What's the story?</div>
    <div class="card-sub">Enter a topic or question. We'll find the debates, evidence, and angles that make it worth writing.</div>
</div>
""", unsafe_allow_html=True)

topic = st.text_input(
    "Topic",
    placeholder="e.g. content gap analysis, AI in hiring, B2B influencer marketing",
    label_visibility="collapsed"
)

# ── Run button ────────────────────────────────────────────────────────────────
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
can_run = bool(topic and keys_ok)

col_btn, col_hint = st.columns([1, 2])
with col_btn:
    run_btn = st.button(
        "🔍  Find the Angle",
        type="primary",
        disabled=not can_run,
        help="Fill in a keyword and both API keys to start"
    )
with col_hint:
    if not anthropic_key:
        st.markdown('<span class="badge badge-warn">👈 Add your Anthropic key in the sidebar</span>', unsafe_allow_html=True)
    elif not serper_key:
        st.markdown('<span class="badge badge-warn">👈 Add your Serper key in the sidebar</span>', unsafe_allow_html=True)
    elif not topic:
        st.markdown('<span class="badge badge-info">Enter a keyword above to continue</span>', unsafe_allow_html=True)
    elif can_run:
        st.markdown('<span class="badge badge-success">✓ Ready — enter keyword and hit Start</span>', unsafe_allow_html=True)

# ── Pipeline ──────────────────────────────────────────────────────────────────
if run_btn and can_run:

    # STEP 1: Research
    st.session_state.pipeline_step = 1
    render_progress(progress_placeholder, 1)

    with st.status("🔍 Gathering research across sources...", expanded=True) as status1:
        def scout_progress(msg):
            st.write(f"→ {msg}")

        scout_data = run_scout(topic, serper_key, progress_callback=scout_progress)

        st.write(f"📰 {len(scout_data.get('web_results', []))} web results")
        st.write(f"💬 {len(scout_data.get('reddit_results', []))} Reddit threads")
        st.write(f"🏢 {len(scout_data.get('linkedin_results', []))} LinkedIn posts")
        st.write(f"📰 {len(scout_data.get('news_results', []))} news articles")
        st.write(f"⭐ {len(scout_data.get('review_results', []))} reviews")
        st.write(f"🐦 {len(scout_data.get('twitter_results', []))} X/Twitter results")
        st.write(f"💬 {len(scout_data.get('forum_results', []))} forum results")
        st.write(f"❓ {len(scout_data.get('people_also_ask', []))} PAA questions")
        st.write(f"🔗 {len(scout_data.get('related_terms', []))} related terms")
        status1.update(label="✅ Step 1 complete — Research gathered", state="complete")

    # STEP 2: Brief
    st.session_state.pipeline_step = 2
    render_progress(progress_placeholder, 2)

    with st.status("✍️ Building editorial brief with Claude...", expanded=True) as status2:
        def strategist_progress(msg):
            st.write(f"→ {msg}")

        brief, error = generate_brief(
            topic=topic,
            scout_data=scout_data,
            api_key=anthropic_key,
            power_words=power_words,
            progress_callback=strategist_progress,
        )
        if error:
            st.error(f"Claude failed: {error}")
            status2.update(label="❌ Step 2 failed", state="error")
        else:
            status2.update(label="✅ Step 2 complete — Editorial brief ready", state="complete")

    st.session_state.pipeline_step = 3
    render_progress(progress_placeholder, 3)

    # ── Results ───────────────────────────────────────────────────────────────
    if brief:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.success("✍️ Editorial brief ready. The thesis, debates, and angles are below.")

        # Metrics
        st.markdown(f"""
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-number">{len(scout_data.get('reddit_results', []))}</div>
                <div class="metric-label">Practitioner Voices</div>
            </div>
            <div class="metric-card">
                <div class="metric-number">{len(scout_data.get('linkedin_results', []))}</div>
                <div class="metric-label">Expert Takes</div>
            </div>
            <div class="metric-card">
                <div class="metric-number">{len(scout_data.get('news_results', []))}</div>
                <div class="metric-label">Recent Developments</div>
            </div>
            <div class="metric-card">
                <div class="metric-number">{len(scout_data.get('review_results', []))}</div>
                <div class="metric-label">Real-World Friction</div>
            </div>
            <div class="metric-card">
                <div class="metric-number">{len(scout_data.get('people_also_ask', []))}</div>
                <div class="metric-label">Audience Questions</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Tabs
        tab_brief, tab_web, tab_reddit, tab_social, tab_news, tab_reviews = st.tabs([
            "✍️  Editorial Brief",
            "🔍  Context",
            "💬  Practitioner Voice",
            "🏢  Expert Takes",
            "📰  What Changed",
            "⭐  Real-World Friction",
        ])

        # ── Brief ─────────────────────────────────────────────────────────────
        with tab_brief:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(brief)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Web ───────────────────────────────────────────────────────────────
        with tab_web:
            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("""
                <div class="card">
                    <div class="card-title">Topic Signals</div>
                    <div class="card-heading">Adjacent angles & questions</div>
                    <div class="card-sub">What surrounds this topic — useful for finding the debates and gaps.</div>
                """, unsafe_allow_html=True)
                chips = ''.join(
                    f'<span class="chip chip-purple">{t}</span>'
                    for t in scout_data.get('related_terms', [])
                )
                st.markdown(f'<div class="chip-wrap">{chips}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown("""
                <div class="card">
                    <div class="card-title">Audience Questions</div>
                    <div class="card-heading">What people are actually asking</div>
                    <div class="card-sub">Curiosity and tension signals — not FAQ targets.</div>
                """, unsafe_allow_html=True)
                for q in scout_data.get('people_also_ask', []):
                    st.markdown(f'<div class="result-card"><div class="result-card-title">❓ {q}</div></div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with col_b:
                st.markdown("""
                <div class="card">
                    <div class="card-title">What's Already Out There</div>
                    <div class="card-heading">Current coverage</div>
                    <div class="card-sub">Use this to identify what's been said to death — and what's missing.</div>
                """, unsafe_allow_html=True)
                for r in scout_data.get('web_results', []):
                    st.markdown(f"""
                    <div class="result-card">
                        <div class="result-card-title">
                            <a href="{r['url']}" target="_blank" style="color:#7C6EE8;text-decoration:none;">{r['title']}</a>
                        </div>
                        <div class="result-card-meta">{r.get('snippet', '')[:200]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        # ── Reddit ────────────────────────────────────────────────────────────
        with tab_reddit:
            col_a, col_b = st.columns(2)
            reddit_items = scout_data.get('reddit_results', [])
            forum_items  = scout_data.get('forum_results', [])

            with col_a:
                st.markdown("""
                <div class="card">
                    <div class="card-title">Reddit Threads</div>
                    <div class="card-heading">Practitioner voice</div>
                    <div class="card-sub">Real opinions, frustrations, and debates — the language your audience actually uses.</div>
                """, unsafe_allow_html=True)
                for r in reddit_items:
                    st.markdown(f"""
                    <div class="result-card">
                        <div class="result-card-title">
                            <a href="{r['url']}" target="_blank" style="color:#7C6EE8;text-decoration:none;">{r['title']}</a>
                        </div>
                        <div class="result-card-meta">{r.get('snippet', '')[:300]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                if not reddit_items:
                    st.info("No Reddit results found.")
                st.markdown('</div>', unsafe_allow_html=True)

            with col_b:
                st.markdown("""
                <div class="card">
                    <div class="card-title">Forum & Discussion Boards</div>
                    <div class="card-heading">More practitioner takes</div>
                    <div class="card-sub">Quora, niche forums, and other sources of unfiltered opinion.</div>
                """, unsafe_allow_html=True)
                for r in forum_items:
                    st.markdown(f"""
                    <div class="result-card">
                        <div class="result-card-title">
                            <a href="{r['url']}" target="_blank" style="color:#7C6EE8;text-decoration:none;">{r['title']}</a>
                        </div>
                        <div class="result-card-meta">{r.get('snippet', '')[:300]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                if not forum_items:
                    st.info("No forum results found.")
                st.markdown('</div>', unsafe_allow_html=True)

        # ── LinkedIn & X ──────────────────────────────────────────────────────
        with tab_social:
            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("""
                <div class="card">
                    <div class="card-title">LinkedIn</div>
                    <div class="card-heading">Expert takes & named opinions</div>
                    <div class="card-sub">Practitioner posts with attribution — useful for debate framing and credible angles.</div>
                """, unsafe_allow_html=True)
                for r in scout_data.get('linkedin_results', []):
                    st.markdown(f"""
                    <div class="result-card">
                        <div class="result-card-title">
                            <a href="{r['url']}" target="_blank" style="color:#7C6EE8;text-decoration:none;">{r['title']}</a>
                        </div>
                        <div class="result-card-meta">{r.get('snippet', '')[:250]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                if not scout_data.get('linkedin_results'):
                    st.info("No LinkedIn results found.")
                st.markdown('</div>', unsafe_allow_html=True)

            with col_b:
                st.markdown("""
                <div class="card">
                    <div class="card-title">X / Twitter</div>
                    <div class="card-heading">Contrarian takes & live debates</div>
                    <div class="card-sub">Fast-moving opinions, industry friction, and the angles practitioners actually argue about.</div>
                """, unsafe_allow_html=True)
                for r in scout_data.get('twitter_results', []):
                    st.markdown(f"""
                    <div class="result-card">
                        <div class="result-card-title">
                            <a href="{r['url']}" target="_blank" style="color:#7C6EE8;text-decoration:none;">{r['title']}</a>
                        </div>
                        <div class="result-card-meta">{r.get('snippet', '')[:250]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                if not scout_data.get('twitter_results'):
                    st.info("No X/Twitter results found.")
                st.markdown('</div>', unsafe_allow_html=True)

        # ── News ──────────────────────────────────────────────────────────────
        with tab_news:
            st.markdown("""
            <div class="card">
                <div class="card-title">What Changed Recently</div>
                <div class="card-heading">Industry developments & timeliness hooks</div>
                <div class="card-sub">What shifted in the last 6-12 months — the "why now" for your article.</div>
            """, unsafe_allow_html=True)
            news_cols = st.columns(2)
            news_items = scout_data.get('news_results', [])
            for i, r in enumerate(news_items):
                with news_cols[i % 2]:
                    date_str = f'<div class="result-card-date">{r["date"]}</div>' if r.get("date") else ""
                    st.markdown(f"""
                    <div class="result-card">
                        <div class="result-card-title">
                            <a href="{r['url']}" target="_blank" style="color:#7C6EE8;text-decoration:none;">{r['title']}</a>
                        </div>
                        <div class="result-card-meta">{r.get('snippet', '')[:200]}</div>
                        {date_str}
                    </div>
                    """, unsafe_allow_html=True)
            if not news_items:
                st.info("No news results found.")
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Reviews ───────────────────────────────────────────────────────────
        with tab_reviews:
            st.markdown("""
            <div class="card">
                <div class="card-title">Real-World Friction — G2 / Capterra / Trustpilot</div>
                <div class="card-heading">What actually breaks down in practice</div>
                <div class="card-sub">User complaints and failures — the gap between what's promised and what's delivered.</div>
            """, unsafe_allow_html=True)
            review_cols = st.columns(2)
            review_items = scout_data.get('review_results', [])
            for i, r in enumerate(review_items):
                with review_cols[i % 2]:
                    st.markdown(f"""
                    <div class="result-card">
                        <div class="result-card-title">
                            <a href="{r['url']}" target="_blank" style="color:#7C6EE8;text-decoration:none;">{r['title']}</a>
                        </div>
                        <div class="result-card-meta">{r.get('snippet', '')[:250]}</div>
                    </div>
                    """, unsafe_allow_html=True)
            if not review_items:
                st.info("No review results found.")
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Downloads ─────────────────────────────────────────────────────────
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="card">
            <div class="card-title">Export</div>
            <div class="card-heading">Download your editorial brief</div>
            <div class="card-sub">Save the Resource Bank and editorial brief in your preferred format.</div>
        </div>
        """, unsafe_allow_html=True)

        slug = topic[:30].replace(' ', '_')
        dl1, dl2, dl3 = st.columns(3)

        with dl1:
            st.download_button(
                label="📋 Brief (.md)",
                data=brief,
                file_name=f"content_brief_{slug}.md",
                mime="text/markdown"
            )

        with dl2:
            full_report = f"# Editorial Brief — {topic}\n\n{brief}"
            st.download_button(
                label="📄 Full Report (.md)",
                data=full_report,
                file_name=f"research_report_{slug}.md",
                mime="text/markdown"
            )

        with dl3:
            export_data = {
                "topic": topic,
                "related_terms": scout_data.get("related_terms", []),
                "people_also_ask": scout_data.get("people_also_ask", []),
                "reddit_results": scout_data.get("reddit_results", []),
                "linkedin_results": scout_data.get("linkedin_results", []),
                "news_results": scout_data.get("news_results", []),
                "review_results": scout_data.get("review_results", []),
                "twitter_results": scout_data.get("twitter_results", []),
                "forum_results": scout_data.get("forum_results", []),
                "brief": brief,
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
    Powered by <a href="https://anthropic.com">Claude (Anthropic)</a> · <a href="https://serper.dev">Serper.dev</a>
</div>
""", unsafe_allow_html=True)
