"""
app.py — Interview Integrity Analyzer
══════════════════════════════════════
Home page and session state initialization.
TCS Tech Day Hackathon Prototype.

Run with:
    streamlit run app.py
"""

import streamlit as st
import sys
import os

# ── Path setup (ensure local modules are importable) ──────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

# ── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title = "Interview Integrity Analyzer",
    page_icon  = "🔍",
    layout     = "wide",
    initial_sidebar_state = "expanded",
)

# ── Load dotenv (optional — for local .env file support) ─────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from utils.styles import get_css, sidebar_branding

# ── Inject CSS ────────────────────────────────────────────────────────────────
st.markdown(get_css(), unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Session State Initialization
# Initialize ALL keys here once at app load so all pages can access them safely.
# ─────────────────────────────────────────────────────────────────────────────
_defaults = {
    "resume_text":         "",
    "candidate_name":      "",
    "selected_candidate":  None,      # dict from sample_candidates.py
    "interview_question":  "",
    "candidate_answer":    "",
    "transcript_notes":    "",
    "behavioral_obs": {
        "eye_contact":        "Good",
        "lip_sync":           "Matched",
        "voice_behaviour":    "Natural",
        "prompting_detected": "No",
    },
    "analysis_result":     None,      # dict from gemini_service
    "risk_result":         None,      # RiskResult dataclass
    "analysis_complete":   False,
    "gemini_api_key":      os.getenv("GEMINI_API_KEY", ""),
}

for key, default in _defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(sidebar_branding(), unsafe_allow_html=True)

    st.markdown("#### ⚙️ Configuration")
    api_key_input = st.text_input(
        "Gemini API Key",
        value       = st.session_state.gemini_api_key,
        type        = "password",
        placeholder = "AIza...",
        help        = "Get your key at aistudio.google.com/app/apikey",
    )
    if api_key_input:
        st.session_state.gemini_api_key = api_key_input

    if st.session_state.gemini_api_key:
        st.markdown(
            "<div style='color:#10b981; font-size:0.8rem;'>✅ API Key configured</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div style='color:#f59e0b; font-size:0.8rem;'>⚠️ No API Key — using fallback mode</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown("#### 🧭 Workflow")
    st.markdown("""
<div style='font-size:0.82rem; color:#94a3b8; line-height:2;'>
  📄 <b>Step 1</b> — Candidate Profile<br/>
  🔍 <b>Step 2</b> — Interview Analysis<br/>
  📋 <b>Step 3</b> — Download Report
</div>
""", unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown("#### 📊 Session Status")
    if st.session_state.candidate_name:
        st.success(f"Candidate: **{st.session_state.candidate_name}**")
    else:
        st.info("No candidate loaded yet.")

    if st.session_state.analysis_complete:
        risk = st.session_state.risk_result
        if risk:
            level = risk.risk_level if hasattr(risk, "risk_level") else risk.get("risk_level", "—")
            score = risk.risk_score if hasattr(risk, "risk_score") else risk.get("risk_score", 0)
            emoji = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}.get(level, "⚪")
            st.markdown(
                f"<div style='color:#94a3b8; font-size:0.82rem;'>"
                f"Risk: <b style='color:#f1f5f9;'>{emoji} {level} ({score}/100)</b>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # Reset session button
    st.markdown("<br/>", unsafe_allow_html=True)
    if st.button("🔄 Reset Session", use_container_width=True):
        for key, default in _defaults.items():
            st.session_state[key] = default
        st.rerun()

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:0.7rem; color:#475569; text-align:center;'>"
        "TCS Tech Day Hackathon<br/>Prototype — Not for Production Use"
        "</div>",
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# Home Page Content
# ─────────────────────────────────────────────────────────────────────────────

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-container">
    <div class="hero-title">🔍 Interview Integrity Analyzer</div>
    <div class="hero-subtitle">
        AI-assisted prototype for identifying possible interview impersonation,
        scripted responses, and AI-generated answers in online hiring processes.
    </div>
    <div class="disclaimer-badge">
        ⚖️ Decision Support Tool Only &nbsp;—&nbsp; This system does not make hiring decisions
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

# ── Feature Cards ─────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

features = [
    ("📄", "Resume Analysis",    "Parse and extract candidate profile data from PDF or text resumes."),
    ("💬", "Interview Q&A",      "Input interview questions, answers, and transcript notes for analysis."),
    ("🤖", "Gemini AI Engine",   "Google Gemini 2.5 Flash compares claimed skills with actual responses."),
    ("📊", "Risk Scoring",       "Rule-based engine calculates a 0–100 integrity risk score with explanations."),
]

for col, (icon, title, desc) in zip([c1, c2, c3, c4], features):
    with col:
        st.markdown(
            f"""<div class="feature-card">
                <div class="feature-icon">{icon}</div>
                <div class="feature-title">{title}</div>
                <div class="feature-desc">{desc}</div>
            </div>""",
            unsafe_allow_html=True,
        )

st.markdown("<br/>", unsafe_allow_html=True)

# ── Workflow Steps ────────────────────────────────────────────────────────────
st.markdown("### How It Works")
wf_col1, wf_col2 = st.columns([1, 1])

with wf_col1:
    for step in [
        ("1", "Load Candidate Resume",
         "Select one of 5 synthetic sample profiles or upload your own PDF/TXT resume file."),
        ("2", "Enter Interview Details",
         "Input the interview question, candidate's answer, transcript notes, and behavioral observations."),
    ]:
        st.markdown(
            f"""<div class="workflow-step">
                <div class="workflow-num">{step[0]}</div>
                <div class="workflow-text">
                    <h4>{step[1]}</h4>
                    <p>{step[2]}</p>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

with wf_col2:
    for step in [
        ("3", "Run AI Analysis",
         "Gemini 2.5 Flash analyzes the resume against the interview response. "
         "The rule-based engine calculates a risk score with factor breakdown."),
        ("4", "Download PDF Report",
         "Generate and download a professional interview integrity report for recruiter review."),
    ]:
        st.markdown(
            f"""<div class="workflow-step">
                <div class="workflow-num">{step[0]}</div>
                <div class="workflow-text">
                    <h4>{step[1]}</h4>
                    <p>{step[2]}</p>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

st.markdown("<br/>", unsafe_allow_html=True)

# ── CTA Buttons ───────────────────────────────────────────────────────────────
btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])

with btn_col1:
    if st.button("🚀 Start Analysis", use_container_width=True):
        st.switch_page("pages/1_Candidate_Profile.py")

with btn_col2:
    if st.button("👥 View Sample Candidates", use_container_width=True):
        st.switch_page("pages/1_Candidate_Profile.py")

with btn_col3:
    if st.button("📄 View Report", use_container_width=True, disabled=not st.session_state.analysis_complete):
        st.switch_page("pages/3_Report.py")

st.markdown("<br/>", unsafe_allow_html=True)

# ── Key System Notes ──────────────────────────────────────────────────────────
st.markdown("---")
info_col1, info_col2, info_col3 = st.columns(3)

with info_col1:
    st.markdown("""
<div class="info-box">
<b>🔒 Privacy by Design</b><br/><br/>
No real biometric data is collected.
Behavioral observations are entered manually
by the recruiter as simulated inputs.
</div>""", unsafe_allow_html=True)

with info_col2:
    st.markdown("""
<div class="info-box">
<b>⚖️ Human Oversight Required</b><br/><br/>
All risk scores and AI explanations require
human review. This tool is a <i>support aid</i>
— not a decision engine.
</div>""", unsafe_allow_html=True)

with info_col3:
    st.markdown("""
<div class="info-box">
<b>🧪 Hackathon Prototype</b><br/><br/>
Built for TCS Tech Day at Vidyavardhini
College of Engineering, Vasai.
Theme: AI + Cyber Defense.
</div>""", unsafe_allow_html=True)
