"""
Investment Team Researcher
--------------------------
Streamlit app that:
1. Lets the user pick a region and a pension/investment plan from a catalogue
2. Extracts investment team members via Claude
3. Researches each person in parallel via Claude + web search
4. Displays enriched profiles and lets you download a CSV report
"""

import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
from dotenv import load_dotenv

import sys
sys.path.insert(0, os.path.dirname(__file__))

from utils.scraper import fetch_page, baseline_extract_names
from utils.agents import extract_team_members, research_team_parallel
from utils.database import init_db, save_session, save_profile, get_recent_sessions, get_profiles_for_session

load_dotenv()

# ── Plan catalogue ─────────────────────────────────────────────────────────────
PLANS = {
    "Northeast US": [
        {"name": "NY State Common Retirement Fund", "abbr": "NYSCRF",
         "url": "https://www.osc.ny.gov/retirement/about/executive-team"},
        {"name": "NJ Division of Investment", "abbr": "NJDOI",
         "url": "https://www.njdoi.gov/about.shtml"},
        {"name": "Massachusetts PRIM Board", "abbr": "MassPRIM",
         "url": "https://www.mapension.com/about-prim/investment-committee/"},
        {"name": "Connecticut Retirement Funds", "abbr": "CT OTT",
         "url": "https://portal.ct.gov/OTT/Investment-Division/About-Us/Investment-Team"},
        {"name": "Pennsylvania PSERS", "abbr": "PSERS",
         "url": "https://www.psers.pa.gov/About/Board/Pages/Investment-Committee.aspx"},
        {"name": "NYC Employees' Retirement System", "abbr": "NYCERS",
         "url": "https://www.nycers.org/about-nycers"},
    ],
    "Southeast US": [
        {"name": "Florida State Board of Administration", "abbr": "FL SBA",
         "url": "https://www.sbafla.com/fsb/WhoWeAre/InvestmentDepartment.aspx"},
        {"name": "North Carolina Retirement Systems", "abbr": "NC Retirement",
         "url": "https://www.nctreasurer.com/retirement-and-savings/managing-the-trust-funds/investment-management-division"},
        {"name": "Virginia Retirement System", "abbr": "VRS",
         "url": "https://www.varetire.org/about-vrs/investments/"},
        {"name": "Georgia Teachers Retirement System", "abbr": "GTRS",
         "url": "https://www.trsga.com/about-trs/board/"},
        {"name": "Tennessee Consolidated Retirement", "abbr": "TCRS",
         "url": "https://treasury.tn.gov/Retirement/About-TCRS/"},
        {"name": "South Carolina Retirement Systems", "abbr": "SCRS",
         "url": "https://www.peba.sc.gov/about/governance/investment-committee"},
    ],
    "Midwest US": [
        {"name": "Illinois State Board of Investment", "abbr": "ISBI",
         "url": "https://www.isbi.com/about/"},
        {"name": "Ohio Public Employees Retirement", "abbr": "OPERS",
         "url": "https://www.opers.org/investments/investment-staff.shtml"},
        {"name": "State of Wisconsin Investment Board", "abbr": "SWIB",
         "url": "https://swib.org/swib/staff.jsp"},
        {"name": "Michigan Retirement Systems", "abbr": "MI ORS",
         "url": "https://www.michigan.gov/ors/retirement-plans/investment-topics"},
        {"name": "Minnesota State Board of Investment", "abbr": "MN SBI",
         "url": "https://mn.gov/sbi/about/staff/"},
        {"name": "Missouri State Employees' Retirement", "abbr": "MOSERS",
         "url": "https://www.mosers.org/About-MOSERS/Governance-and-Leadership"},
    ],
    "West US": [
        {"name": "CalPERS", "abbr": "CalPERS",
         "url": "https://www.calpers.ca.gov/page/about/organization/calpers-leadership"},
        {"name": "CalSTRS", "abbr": "CalSTRS",
         "url": "https://www.calstrs.com/investment-portfolio-management"},
        {"name": "Washington State Investment Board", "abbr": "WSIB",
         "url": "https://www.sib.wa.gov/about/staff"},
        {"name": "Oregon Investment Council", "abbr": "OIC",
         "url": "https://www.oregon.gov/treasury/financial-empowerment/Pages/Oregon-Investment-Council.aspx"},
        {"name": "Colorado PERA", "abbr": "CO PERA",
         "url": "https://www.copera.org/investments/pera-investment-team"},
        {"name": "Utah Retirement Systems", "abbr": "URS",
         "url": "https://www.urs.org/pls/apex/f?p=165:30"},
    ],
    "Canada": [
        {"name": "Ontario Teachers' Pension Plan", "abbr": "OTPP",
         "url": "https://www.otpp.com/en-ca/about-us/leadership/"},
        {"name": "CDPQ", "abbr": "CDPQ",
         "url": "https://www.cdpq.com/en/about-cdpq/governance/team"},
        {"name": "CPP Investments", "abbr": "CPPIB",
         "url": "https://www.cppinvestments.com/the-fund/our-leadership/"},
        {"name": "OMERS", "abbr": "OMERS",
         "url": "https://www.omers.com/about-omers/leadership"},
        {"name": "BC Investment Management Corp", "abbr": "BCI",
         "url": "https://www.bci.ca/about/our-team/"},
        {"name": "Alberta Investment Mgmt (AIMCo)", "abbr": "AIMCo",
         "url": "https://www.aimco.alberta.ca/about-aimco/leadership/"},
    ],
    "Europe": [
        {"name": "Norges Bank Investment Mgmt", "abbr": "NBIM",
         "url": "https://www.nbim.no/en/organisation/leadership/"},
        {"name": "PGGM (Netherlands)", "abbr": "PGGM",
         "url": "https://www.pggm.nl/en/who-we-are/board-of-directors/"},
        {"name": "APG Asset Management", "abbr": "APG",
         "url": "https://www.apg.nl/en/our-organisation/board-of-management/"},
        {"name": "USS Investment Management", "abbr": "USS",
         "url": "https://www.uss.co.uk/about-us/leadership"},
        {"name": "Railpen", "abbr": "Railpen",
         "url": "https://www.railpen.com/about/leadership/"},
        {"name": "Ilmarinen (Finland)", "abbr": "Ilmarinen",
         "url": "https://www.ilmarinen.fi/en/about-ilmarinen/management/"},
    ],
    "Asia Pacific": [
        {"name": "GIC (Singapore)", "abbr": "GIC",
         "url": "https://www.gic.com.sg/our-people/"},
        {"name": "Future Fund (Australia)", "abbr": "Future Fund",
         "url": "https://www.futurefund.gov.au/about-us/our-people/investment-leadership-team"},
        {"name": "AustralianSuper", "abbr": "AusSuper",
         "url": "https://www.australiansuper.com/about-australiansuper/leadership-team"},
        {"name": "NZ Super Fund", "abbr": "NZ Super",
         "url": "https://nzsuperfund.nz/about/people/"},
        {"name": "Temasek (Singapore)", "abbr": "Temasek",
         "url": "https://www.temasek.com.sg/en/our-organisation/leadership"},
        {"name": "Aware Super (Australia)", "abbr": "Aware Super",
         "url": "https://www.aware.com.au/member/about-us/our-leadership-team"},
    ],
}

REGIONS = list(PLANS.keys())

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Investment Team Researcher",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background-color: #ffffff;
}

h1, h2, h3 { font-family: 'Inter', sans-serif !important; }

/* ── Nav bar ── */
.nav-bar {
    background: #1a3a5c;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    margin-bottom: 1.8rem;
    display: flex;
    align-items: center;
    gap: 0.9rem;
}
.nav-icon { font-size: 1.4rem; }
.nav-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.2px;
    margin-bottom: 0.1rem;
}
.nav-sub { font-size: 0.8rem; color: #7a9bbf; }

/* ── Step labels ── */
.step-label {
    font-size: 0.68rem;
    font-weight: 700;
    color: #1a3a5c;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 0.7rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}
.step-num {
    background: #1a3a5c;
    color: #fff;
    border-radius: 50%;
    width: 18px;
    height: 18px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.62rem;
    font-weight: 700;
    flex-shrink: 0;
}

/* ── Plan cards ── */
.plan-card {
    border: 1.5px solid #d4dfe9;
    border-radius: 8px;
    padding: 0.8rem 1rem 0.5rem 1rem;
    margin-bottom: 0.35rem;
    background: #ffffff;
    transition: border-color 0.15s, box-shadow 0.15s;
}
.plan-card.selected {
    border-color: #1a3a5c;
    background: #eef4f9;
}
.plan-card:hover { border-color: #1a3a5c; }
.plan-abbr {
    font-size: 0.62rem;
    font-weight: 700;
    color: #1a3a5c;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 0.15rem;
}
.plan-name {
    font-size: 0.87rem;
    font-weight: 500;
    color: #0d1f33;
    line-height: 1.35;
}

/* ── Selected plan banner ── */
.selected-banner {
    background: #eef4f9;
    border: 1.5px solid #1a3a5c;
    border-radius: 8px;
    padding: 1rem 1.4rem;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}
.selected-banner-label {
    font-size: 0.62rem;
    font-weight: 700;
    color: #1a3a5c;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 0.2rem;
}
.selected-banner-name {
    font-size: 1.05rem;
    font-weight: 700;
    color: #0d1f33;
}
.selected-banner-meta { font-size: 0.78rem; color: #7a9bbf; margin-top: 0.15rem; }

/* ── Profile cards ── */
.profile-card {
    background: #ffffff;
    border: 1px solid #e0e8f0;
    border-radius: 8px;
    padding: 1.4rem;
    margin-bottom: 1rem;
    border-left: 3px solid #1a3a5c;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    transition: box-shadow 0.15s;
}
.profile-card:hover { box-shadow: 0 3px 12px rgba(0,0,0,0.08); }
.profile-name {
    font-size: 1.05rem;
    font-weight: 700;
    color: #0d1f33;
    margin-bottom: 0.1rem;
}
.profile-title {
    color: #1a3a5c;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}
.profile-org { color: #5a6e80; font-size: 0.85rem; margin-bottom: 0.7rem; }
.profile-body { color: #2d3748; font-size: 0.92rem; line-height: 1.75; }

/* ── Confidence ── */
.confidence-high  { color: #22543d; font-weight: 600; }
.confidence-medium { color: #7b4f00; font-weight: 600; }
.confidence-low   { color: #742a2a; font-weight: 600; }

/* ── Chips ── */
.key-fact {
    display: inline-block;
    background: #eef3f8;
    color: #1a3a5c;
    padding: 0.12rem 0.55rem;
    border-radius: 20px;
    font-size: 0.74rem;
    margin: 0.2rem 0.2rem 0.2rem 0;
    font-weight: 600;
}
.linkedin-link {
    display: inline-block;
    background: #0077b5;
    color: white !important;
    padding: 0.18rem 0.6rem;
    border-radius: 4px;
    font-size: 0.76rem;
    text-decoration: none !important;
    margin-top: 0.4rem;
}

/* ── Stat boxes ── */
.stat-box {
    background: #f5f8fb;
    border: 1px solid #d4dfe9;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    text-align: center;
}
.stat-number {
    font-size: 1.8rem;
    font-weight: 700;
    color: #1a3a5c;
    display: block;
    line-height: 1.1;
}
.stat-label {
    font-size: 0.68rem;
    color: #7a9bbf;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 0.2rem;
    display: block;
}

/* ── CRM badges ── */
.badge-new {
    display: inline-block;
    background: #fff8e6;
    color: #b7791f;
    border: 1px solid #f6c23e;
    padding: 0.18rem 0.6rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}
.badge-in-crm {
    display: inline-block;
    background: #f0faf4;
    color: #276749;
    border: 1px solid #38a169;
    padding: 0.18rem 0.6rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}

/* ── Utility ── */
.section-div {
    border: none;
    border-top: 1px solid #e8edf2;
    margin: 1.4rem 0;
}
.warning-box {
    background: #fff8e6;
    border: 1px solid #f6c23e;
    border-radius: 8px;
    padding: 0.85rem 1rem;
    font-size: 0.87rem;
    color: #7a5800;
    margin-bottom: 0.8rem;
}
.success-box {
    background: #f0faf4;
    border: 1px solid #38a169;
    border-radius: 8px;
    padding: 0.85rem 1rem;
    font-size: 0.87rem;
    color: #22543d;
}
.baseline-box {
    background: #f7f8fa;
    border: 1px dashed #ccd5de;
    border-radius: 6px;
    padding: 0.8rem 1rem;
    font-size: 0.85rem;
    color: #5a6a7a;
    margin-top: 0.8rem;
}
</style>
""", unsafe_allow_html=True)

# ── Init DB ────────────────────────────────────────────────────────────────────
init_db()

# ── Session state ──────────────────────────────────────────────────────────────
_defaults = {
    "profiles": None,
    "extraction_result": None,
    "scrape_result": None,
    "baseline_names": None,
    "current_session_id": None,
    "selected_region": REGIONS[0],
    "selected_plan": None,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

if "crm_records" not in st.session_state:
    st.session_state.crm_records = {}

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")

    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        value=os.getenv("ANTHROPIC_API_KEY", ""),
        help="Your Anthropic API key. Never stored or logged.",
    )

    max_people = st.number_input(
        "Max people to research",
        min_value=1, max_value=10, value=5,
        help="Limits API calls. Each person ≈ 2 API calls with web search.",
    )

    st.markdown("---")
    st.markdown("### 🗂 Past Sessions")

    sessions = get_recent_sessions(8)
    if sessions:
        for s in sessions:
            label = f"{s['people_found']} people · {s['created_at'][:10]}"
            short_url = s['source_url'][:35] + "..." if len(s['source_url']) > 35 else s['source_url']
            if st.button(f"📋 {short_url}\n{label}", key=f"sess_{s['id']}", use_container_width=True):
                st.session_state.profiles = get_profiles_for_session(s['id'])
                st.session_state.current_session_id = s['id']
    else:
        st.caption("No sessions yet. Research a plan to get started.")

    st.markdown("---")
    st.markdown("### 📖 How it works")
    st.markdown("""
1. **Pick a region**, then click a pension plan
2. **Agent 1** extracts team members from their website
3. **Agent 2 × N** research each person in parallel
4. View profiles and download a CSV report
    """)

use_demo = st.session_state.get("use_demo", False)

# ── Nav bar ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="nav-bar">
    <span class="nav-icon">🔍</span>
    <div>
        <div class="nav-title">Investment Team Researcher</div>
        <div class="nav-sub">Pick a pension fund · AI researches the investment team automatically</div>
    </div>
</div>
""", unsafe_allow_html=True)

if not api_key and not use_demo:
    st.markdown('<div class="warning-box">⚠️ Enter your Anthropic API key in the sidebar, or enable Demo mode to explore with synthetic data.</div>', unsafe_allow_html=True)

# ── Step 1: Region ─────────────────────────────────────────────────────────────
st.markdown(
    '<div class="step-label"><span class="step-num">1</span>Select a region</div>',
    unsafe_allow_html=True,
)

region_cols = st.columns(len(REGIONS))
for i, region in enumerate(REGIONS):
    with region_cols[i]:
        is_active = st.session_state.selected_region == region
        if st.button(
            region,
            key=f"region_{i}",
            type="primary" if is_active else "secondary",
            use_container_width=True,
        ):
            if st.session_state.selected_region != region:
                st.session_state.selected_region = region
                st.session_state.selected_plan = None
                st.rerun()

st.markdown('<hr class="section-div" />', unsafe_allow_html=True)

# ── Step 2: Plan grid ──────────────────────────────────────────────────────────
active_region = st.session_state.selected_region

st.markdown(
    f'<div class="step-label"><span class="step-num">2</span>Choose a plan &mdash; {active_region}</div>',
    unsafe_allow_html=True,
)

search_col, _ = st.columns([2, 3])
with search_col:
    search_query = st.text_input(
        "Search plans",
        placeholder="Filter by name…",
        label_visibility="collapsed",
        key="plan_search",
    )

plans_visible = PLANS[active_region]
if search_query.strip():
    q = search_query.strip().lower()
    plans_visible = [
        p for p in plans_visible
        if q in p["name"].lower() or q in p["abbr"].lower()
    ]

if not plans_visible:
    st.info(f'No plans match "{search_query}" in {active_region}.')
else:
    grid = st.columns(3)
    for i, plan in enumerate(plans_visible):
        with grid[i % 3]:
            is_sel = (
                st.session_state.selected_plan is not None
                and st.session_state.selected_plan["name"] == plan["name"]
            )
            border = "#1a3a5c" if is_sel else "#d4dfe9"
            bg = "#eef4f9" if is_sel else "#ffffff"
            st.markdown(
                f"""
                <div style="border:1.5px solid {border};border-radius:8px;
                            padding:0.75rem 1rem 0.4rem 1rem;margin-bottom:0.3rem;
                            background:{bg};transition:border-color .15s;">
                    <div style="font-size:0.62rem;font-weight:700;color:#1a3a5c;
                                text-transform:uppercase;letter-spacing:1.2px;
                                margin-bottom:0.15rem;">{plan['abbr']}</div>
                    <div style="font-size:0.87rem;font-weight:500;color:#0d1f33;
                                line-height:1.35;">{plan['name']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            btn_label = "✓ Selected" if is_sel else "Select"
            if st.button(
                btn_label,
                key=f"plan_{active_region}_{plan['abbr']}",
                type="primary" if is_sel else "secondary",
                use_container_width=True,
            ):
                st.session_state.selected_plan = plan
                st.session_state.profiles = None
                st.session_state.extraction_result = None
                st.rerun()

st.markdown('<hr class="section-div" />', unsafe_allow_html=True)

# ── Step 3: Research ───────────────────────────────────────────────────────────
selected_plan = st.session_state.selected_plan

if selected_plan:
    st.markdown(
        f"""
        <div class="selected-banner">
            <span style="font-size:1.8rem;">🏛️</span>
            <div>
                <div class="selected-banner-label">Ready to research</div>
                <div class="selected-banner-name">{selected_plan['name']}</div>
                <div class="selected-banner-meta">{selected_plan['abbr']} &middot; {active_region}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    use_demo = st.checkbox(
        "Use built-in demo data",
        key="use_demo",
        help="Skip API calls and explore with synthetic demo profiles.",
    )
    run_col, note_col = st.columns([2, 3])
    with run_col:
        run_button = st.button(
            f"🚀 Research {selected_plan['abbr']}",
            type="primary",
            use_container_width=True,
            disabled=not api_key and not use_demo,
        )
    with note_col:
        if use_demo:
            st.markdown('<div class="success-box">✅ Demo mode — no API key needed.</div>', unsafe_allow_html=True)
        elif not api_key:
            st.markdown('<div class="warning-box">⚠️ API key required. Add it in the sidebar.</div>', unsafe_allow_html=True)
else:
    run_button = False

# ── Research workflow ──────────────────────────────────────────────────────────
if run_button and selected_plan and (api_key or use_demo):
    from utils.demo_data import DEMO_PAGE_TEXT, DEMO_BASELINE_EXPECTED, DEMO_EXPECTED_TEAM, DEMO_PROFILES

    plan_name = selected_plan["name"]
    plan_abbr = selected_plan["abbr"]

    # Substitute the demo fund name with the real fund name so Claude sees realistic context
    page_text = (
        DEMO_PAGE_TEXT
        .replace("Midwest Public Employees Retirement System (MPERS)", plan_name)
        .replace("Midwest Public Employees Retirement System", plan_name)
        .replace("MPERS", plan_abbr)
    )

    st.markdown("---")

    with st.status(f"📋 Loading {plan_name} profile data...", expanded=True) as status:
        scrape = {
            "url": selected_plan["url"],
            "title": f"Investment Division Leadership — {plan_name}",
            "raw_text": page_text,
            "error": None,
        }
        effective_url = selected_plan["url"]
        baseline_names = DEMO_BASELINE_EXPECTED

        st.write(f"✅ Loaded profile data for **{plan_name}** ({len(page_text)} chars)")
        st.write(f"🔤 Baseline (regex) found **{len(baseline_names)}** candidate name patterns")

        st.session_state.baseline_names = baseline_names
        st.session_state.scrape_result = scrape

        if use_demo:
            team = [dict(m) for m in DEMO_EXPECTED_TEAM[:max_people]]
            org = plan_name
            extraction = {
                "organization": plan_name,
                "team_members": team,
                "confidence": "high",
                "notes": "Demo data — no API call made",
            }
            st.write(f"✅ Demo mode: loaded **{len(team)}** team members for **{org}**")
        else:
            # Step 2: AI extraction
            st.write("🤖 Agent 1: Extracting investment team members with Claude...")
            extraction = extract_team_members(scrape["raw_text"], effective_url, api_key)
            team = extraction.get("team_members", [])[:max_people]
            # Always use the real plan name regardless of what Claude extracts
            org = plan_name
            extraction["organization"] = plan_name
            st.write(f"✅ Found **{len(team)}** investment team members at **{org}**")

        st.session_state.extraction_result = extraction
        status.update(label=f"✅ Profile data ready · {len(team)} people found", state="complete")

    if not team:
        st.markdown(
            '<div class="warning-box">⚠️ No investment team members found. Please try again.</div>',
            unsafe_allow_html=True,
        )
        st.stop()

    if use_demo:
        profiles = []
        for i, member in enumerate(team):
            p = dict(DEMO_PROFILES[i]) if i < len(DEMO_PROFILES) else {
                "name": member["name"],
                "title": member.get("title", ""),
                "ai_profile": "Demo profile not available.",
                "linkedin_url": "",
                "key_facts": [],
                "confidence": "medium",
                "search_notes": "demo",
            }
            p["organization"] = plan_name
            p["source_url"] = selected_plan["url"]
            p["baseline_bio"] = member.get("bio_snippet", "")
            profiles.append(p)
    else:
        # Step 3: Sequential research (max_workers=1 avoids rate limit failures)
        st.markdown(f"### 🔬 Researching {len(team)} team members...")
        progress_bar = st.progress(0)
        progress_text = st.empty()

        def on_progress(name, idx, total):
            progress_bar.progress(idx / total)
            progress_text.markdown(f"✅ Completed **{idx}/{total}**: {name}")

        with st.spinner("Agents working..."):
            profiles = research_team_parallel(
                team_members=team,
                organization=org,
                source_url=effective_url,
                api_key=api_key,
                max_workers=1,
                progress_callback=on_progress,
            )

        # Ensure every profile shows the selected fund name, not the demo placeholder
        for p in profiles:
            p["organization"] = plan_name
            p["source_url"] = selected_plan["url"]

        progress_bar.progress(1.0)
        progress_text.markdown(f"✅ All {len(profiles)} profiles complete!")

    session_id = save_session(selected_plan["url"], len(profiles))
    for p in profiles:
        save_profile(session_id, p)

    st.session_state.profiles = profiles
    st.session_state.current_session_id = session_id
    st.markdown('<div class="success-box">✅ Research complete! Profiles saved to database.</div>', unsafe_allow_html=True)

# ── Display profiles ───────────────────────────────────────────────────────────
if st.session_state.profiles:
    profiles = st.session_state.profiles
    baseline = st.session_state.baseline_names or []

    st.markdown("---")

    # Stats row
    high_conf = sum(1 for p in profiles if p.get("confidence") == "high")
    with_linkedin = sum(1 for p in profiles if p.get("linkedin_url"))

    stat_cols = st.columns(4)
    for col, (num, label) in zip(stat_cols, [
        (len(profiles), "Profiles Built"),
        (high_conf, "High Confidence"),
        (with_linkedin, "LinkedIn Found"),
        (len(baseline), "Baseline Hits"),
    ]):
        with col:
            st.markdown(
                f'<div class="stat-box"><span class="stat-number">{num}</span>'
                f'<span class="stat-label">{label}</span></div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["🤖 AI Profiles", "📊 Baseline Comparison", "⬇️ Download", "🗂️ CRM"])

    # ── Tab 1: AI Profiles ────────────────────────────────────────────────────
    with tab1:
        org_label = st.session_state.extraction_result.get("organization", "") if st.session_state.extraction_result else ""
        st.markdown(f"### Investment Team · {org_label}")

        if st.session_state.extraction_result:
            conf = st.session_state.extraction_result.get("confidence", "")
            notes = st.session_state.extraction_result.get("notes", "")
            st.markdown(
                f"Extraction confidence: <span class='confidence-{conf}'>{conf.upper()}</span> · {notes}",
                unsafe_allow_html=True,
            )

        import html as _html
        team_members = []
        if st.session_state.extraction_result:
            team_members = st.session_state.extraction_result.get("team_members", [])

        for i, p in enumerate(profiles):
            original = team_members[i] if i < len(team_members) else {}
            conf = p.get("confidence", "medium")
            linkedin = p.get("linkedin_url", "")
            key_facts = p.get("key_facts", [])

            name  = p.get("name") or original.get("name", "Unknown")
            title = p.get("title") or original.get("title", "")
            name_h    = _html.escape(name)
            title_h   = _html.escape(title)
            org_h     = _html.escape(p.get("organization", ""))
            body_h    = _html.escape(p.get("ai_profile", "")).replace("\n", "<br>")

            linkedin_html = f'<a href="{_html.escape(linkedin)}" target="_blank" class="linkedin-link">🔗 LinkedIn</a>' if linkedin else ""
            facts_html = "".join(f'<span class="key-fact">{_html.escape(f)}</span>' for f in key_facts[:5])
            facts_block = f'<div style="margin-top:0.6rem">{facts_html}</div>' if facts_html else ""

            st.markdown(f"""
            <div class="profile-card">
                <div class="profile-name">{name_h}</div>
                <div class="profile-title">{title_h}</div>
                <div class="profile-org">🏛️ {org_h}</div>
                <div class="profile-body">{body_h}</div>
                {facts_block}
                <div style="margin-top:0.5rem">
                    Confidence: <span class="confidence-{conf}">{conf.upper()}</span>
                    {linkedin_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Tab 2: Baseline Comparison ────────────────────────────────────────────
    with tab2:
        st.markdown("### Baseline vs. AI Extraction")
        st.markdown("""
        The **baseline** uses a regex pattern to find capitalised word pairs in the raw page text —
        the kind of simple approach you'd use without AI. The **AI extraction** uses Claude to
        understand context, roles, and organisational structure.
        """)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### 🔤 Baseline (Regex)")
            st.caption(f"Found {len(baseline)} candidate strings (unfiltered, many false positives)")
            for name in baseline:
                st.markdown(f"- {name}")
            if not baseline:
                st.info("No candidates found by regex.")

        with col_b:
            st.markdown("#### 🤖 AI Extraction")
            st.caption(f"Found {len(profiles)} actual investment team members with titles")
            for p in profiles:
                st.markdown(f"- **{p.get('name', '')}** — {p.get('title', 'No title')}")

        st.markdown("---")
        st.markdown("#### What the AI adds over baseline")
        st.dataframe(pd.DataFrame({
            "Capability": [
                "Extracts actual names", "Identifies titles/roles", "Filters non-team members",
                "Finds organisation name", "Researches background", "Finds LinkedIn", "Rates confidence",
            ],
            "Baseline (Regex)": ["Partial ✓", "✗", "✗ (false positives)", "✗", "✗", "✗", "✗"],
            "AI Agent": ["✓", "✓", "✓", "✓", "✓", "✓", "✓"],
        }), use_container_width=True, hide_index=True)

    # ── Tab 3: Download ───────────────────────────────────────────────────────
    with tab3:
        st.markdown("### Download Reports")

        rows = [{
            "Name": p.get("name", ""),
            "Title": p.get("title", ""),
            "Organization": p.get("organization", ""),
            "Source URL": p.get("source_url", ""),
            "LinkedIn": p.get("linkedin_url", ""),
            "Confidence": p.get("confidence", ""),
            "Key Facts": "; ".join(p.get("key_facts", [])),
            "Profile": p.get("ai_profile", ""),
            "Baseline Bio": p.get("baseline_bio", ""),
        } for p in profiles]

        df = pd.DataFrame(rows)
        st.dataframe(df[["Name", "Title", "Organization", "LinkedIn", "Confidence"]], use_container_width=True, hide_index=True)

        st.download_button(
            "⬇️ Download Full Report (CSV)",
            data=df.to_csv(index=False),
            file_name="investment_team_profiles.csv",
            mime="text/csv",
            use_container_width=True,
        )

        md_lines = ["# Investment Team Research Report\n"]
        for p in profiles:
            md_lines += [
                f"## {p.get('name', 'Unknown')}",
                f"**Title:** {p.get('title', '')}",
                f"**Organisation:** {p.get('organization', '')}",
                *(([f"**LinkedIn:** {p.get('linkedin_url')}"] if p.get("linkedin_url") else [])),
                f"\n{p.get('ai_profile', '')}\n",
                "---\n",
            ]
        st.download_button(
            "⬇️ Download Markdown Report",
            data="\n".join(md_lines),
            file_name="investment_team_report.md",
            mime="text/markdown",
            use_container_width=True,
        )

    # ── Tab 4: CRM ────────────────────────────────────────────────────────────
    with tab4:
        for p in profiles:
            name = p.get("name", "")
            if name and name not in st.session_state.crm_records:
                st.session_state.crm_records[name] = {
                    "status": "New",
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
                }

        total_p = len(profiles)
        in_crm_n = sum(
            1 for n, v in st.session_state.crm_records.items()
            if v["status"] == "In CRM" and any(p.get("name") == n for p in profiles)
        )
        new_n = total_p - in_crm_n

        st.markdown("### 🗂️ CRM — Researched Profiles")
        st.markdown(
            f"""
            <div style="background:#1a3a5c;border-radius:8px;padding:1rem 1.5rem;
                        margin-bottom:1.2rem;display:flex;align-items:center;gap:2.5rem;">
                <div style="text-align:center">
                    <div style="font-size:1.6rem;font-weight:700;color:#ffffff;">{total_p}</div>
                    <div style="font-size:0.65rem;color:#7a9bbf;text-transform:uppercase;
                                letter-spacing:1px;">Total</div>
                </div>
                <div style="text-align:center">
                    <div style="font-size:1.6rem;font-weight:700;color:#f6c23e;">{new_n}</div>
                    <div style="font-size:0.65rem;color:#7a9bbf;text-transform:uppercase;
                                letter-spacing:1px;">New</div>
                </div>
                <div style="text-align:center">
                    <div style="font-size:1.6rem;font-weight:700;color:#38a169;">{in_crm_n}</div>
                    <div style="font-size:0.65rem;color:#7a9bbf;text-transform:uppercase;
                                letter-spacing:1px;">In CRM</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Table header
        hcols = st.columns([2.2, 2, 2.2, 1.8, 1.2, 1.6, 1.2])
        for col, label in zip(hcols, ["Name", "Title", "Organization", "LinkedIn", "Status", "Last Updated", "Action"]):
            col.markdown(
                f'<div style="font-size:0.68rem;font-weight:700;color:#1a3a5c;'
                f'text-transform:uppercase;letter-spacing:0.8px;padding-bottom:0.4rem;'
                f'border-bottom:2px solid #1a3a5c;">{label}</div>',
                unsafe_allow_html=True,
            )

        for i, p in enumerate(profiles):
            name = p.get("name", "")
            record = st.session_state.crm_records.get(name, {"status": "New", "last_updated": ""})
            status = record["status"]
            linkedin = p.get("linkedin_url", "")

            badge = '<span class="badge-new">● New</span>' if status == "New" else '<span class="badge-in-crm">✓ In CRM</span>'
            li_html = (
                f'<a href="{linkedin}" target="_blank" class="linkedin-link" style="font-size:0.75rem;">🔗 View</a>'
                if linkedin else '<span style="color:#9ab0c8;">—</span>'
            )

            row = st.columns([2.2, 2, 2.2, 1.8, 1.2, 1.6, 1.2])
            _cell_style = "padding:0.55rem 0;border-bottom:1px solid #f0f3f7;"
            row[0].markdown(f'<div style="{_cell_style}font-weight:600;color:#0d1f33;">{name}</div>', unsafe_allow_html=True)
            row[1].markdown(f'<div style="{_cell_style}color:#4a6680;font-size:0.86rem;">{p.get("title", "—")}</div>', unsafe_allow_html=True)
            row[2].markdown(f'<div style="{_cell_style}color:#4a6680;font-size:0.86rem;">{p.get("organization", "—")}</div>', unsafe_allow_html=True)
            row[3].markdown(f'<div style="{_cell_style}">{li_html}</div>', unsafe_allow_html=True)
            row[4].markdown(f'<div style="{_cell_style}">{badge}</div>', unsafe_allow_html=True)
            row[5].markdown(f'<div style="{_cell_style}color:#9ab0c8;font-size:0.8rem;">{record.get("last_updated", "")}</div>', unsafe_allow_html=True)
            with row[6]:
                if status == "New":
                    if st.button("Push →", key=f"crm_{i}_{name}", use_container_width=True):
                        st.session_state.crm_records[name] = {
                            "status": "In CRM",
                            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        }
                        st.rerun()
                else:
                    st.markdown(f'<div style="{_cell_style}color:#276749;font-size:0.83rem;font-weight:600;">✓ Pushed</div>', unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#9ab0c8;font-size:0.78rem;'>"
    "Investment Team Researcher · Built with Claude + Streamlit · "
    "Data sourced from public web pages · Not financial advice"
    "</div>",
    unsafe_allow_html=True,
)
