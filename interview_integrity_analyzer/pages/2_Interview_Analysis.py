"""
pages/2_Interview_Analysis.py
──────────────────────────────
Step 2 of 3 — Interview Input, AI Analysis & Risk Scoring.

Recruiters enter:
  • Interview question and candidate answer
  • Transcript notes
  • Behavioral observations (eye contact, lip sync, voice, prompting)

On "Analyze", Gemini 2.5 Flash analyzes resume vs response.
The rule-based risk engine scores all factors and produces a risk dashboard.
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title = "Interview Analysis — Interview Integrity Analyzer",
    page_icon  = "🔍",
    layout     = "wide",
)

import plotly.graph_objects as go
from models.gemini_service  import analyze_interview
from models.risk_engine     import calculate_risk, get_factor_chart_data
from utils.styles           import get_css, sidebar_branding, step_indicator

st.markdown(get_css(), unsafe_allow_html=True)

# ── Ensure session state ──────────────────────────────────────────────────────
if "resume_text"         not in st.session_state: st.session_state.resume_text         = ""
if "candidate_name"      not in st.session_state: st.session_state.candidate_name      = ""
if "selected_candidate"  not in st.session_state: st.session_state.selected_candidate  = None
if "interview_question"  not in st.session_state: st.session_state.interview_question  = ""
if "candidate_answer"    not in st.session_state: st.session_state.candidate_answer    = ""
if "transcript_notes"    not in st.session_state: st.session_state.transcript_notes    = ""
if "behavioral_obs"      not in st.session_state:
    st.session_state.behavioral_obs = {
        "eye_contact": "Good", "lip_sync": "Matched",
        "voice_behaviour": "Natural", "prompting_detected": "No",
    }
if "analysis_result"     not in st.session_state: st.session_state.analysis_result     = None
if "risk_result"         not in st.session_state: st.session_state.risk_result         = None
if "analysis_complete"   not in st.session_state: st.session_state.analysis_complete   = False
if "gemini_api_key"      not in st.session_state: st.session_state.gemini_api_key      = ""

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(sidebar_branding(), unsafe_allow_html=True)
    api_key_input = st.text_input(
        "Gemini API Key", value=st.session_state.gemini_api_key,
        type="password", placeholder="AIza...",
    )
    if api_key_input:
        st.session_state.gemini_api_key = api_key_input

    if st.session_state.gemini_api_key:
        st.markdown("<div style='color:#10b981;font-size:0.8rem;'>✅ API Key configured</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='color:#f59e0b;font-size:0.8rem;'>⚠ Fallback mode (no API key)</div>", unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)
    if st.session_state.candidate_name:
        st.success(f"Candidate: **{st.session_state.candidate_name}**")
    if st.session_state.analysis_complete and st.session_state.risk_result:
        risk = st.session_state.risk_result
        level = risk.risk_level
        score = risk.risk_score
        emoji = {"LOW":"🟢","MEDIUM":"🟡","HIGH":"🔴"}.get(level,"⚪")
        st.markdown(f"<div style='color:#94a3b8;font-size:0.82rem;'>Risk: <b style='color:#f1f5f9;'>{emoji} {level} ({score}/100)</b></div>", unsafe_allow_html=True)

# ── Guard: require resume ─────────────────────────────────────────────────────
if not st.session_state.resume_text:
    st.markdown(step_indicator(2), unsafe_allow_html=True)
    st.warning("⚠️ No candidate resume loaded. Please go back to Step 1 first.")
    if st.button("← Go to Candidate Profile"):
        st.switch_page("pages/1_Candidate_Profile.py")
    st.stop()

# ── Step Indicator ────────────────────────────────────────────────────────────
st.markdown(step_indicator(2), unsafe_allow_html=True)
st.markdown("---")

# ── Page Header ───────────────────────────────────────────────────────────────
candidate_name = st.session_state.candidate_name
st.markdown(f"""
<div class="section-header">
  <h3>🔍 Interview Analysis</h3>
  <p>Analyzing candidate: <strong style='color:#60a5fa;'>{candidate_name}</strong></p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# INPUT SECTION
# ─────────────────────────────────────────────────────────────────────────────
input_col, obs_col = st.columns([3, 2], gap="large")

with input_col:
    # ── Interview Q&A ─────────────────────────────────────────────────────────
    st.markdown("""<div class="section-header"><h3>💬 Interview Q&amp;A</h3></div>""", unsafe_allow_html=True)

    question = st.text_area(
        "Interview Question *",
        value       = st.session_state.interview_question,
        height      = 90,
        placeholder = "e.g. Can you explain how Django handles database migrations and why they are important?",
        help        = "Enter the exact question asked during the interview.",
    )
    st.session_state.interview_question = question

    answer = st.text_area(
        "Candidate's Answer *",
        value       = st.session_state.candidate_answer,
        height      = 200,
        placeholder = (
            "Enter the candidate's verbatim or summarized interview answer here.\n\n"
            "Be as detailed as possible — the AI will compare this against "
            "the skills and projects listed in the resume."
        ),
        help = "Paste or type the candidate's answer as accurately as possible.",
    )
    st.session_state.candidate_answer = answer

    notes = st.text_area(
        "Transcript Notes (optional)",
        value       = st.session_state.transcript_notes,
        height      = 80,
        placeholder = "e.g. Candidate paused frequently. Seemed to read from notes. Switched tabs mid-answer.",
        help        = "Additional recruiter observations not captured in behavioral dropdowns.",
    )
    st.session_state.transcript_notes = notes

with obs_col:
    # ── Behavioral Observations ───────────────────────────────────────────────
    st.markdown("""<div class="section-header"><h3>👁️ Behavioral Observations</h3></div>""", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#94a3b8; font-size:0.8rem; margin-bottom:14px;'>"
        "Simulate video interview behavioral signals using these dropdowns.</p>",
        unsafe_allow_html=True,
    )

    obs = st.session_state.behavioral_obs

    # Eye Contact
    st.markdown("<div class='obs-card'><div class='obs-icon'>👀</div><div class='obs-label'>Eye Contact</div></div>", unsafe_allow_html=True)
    eye_contact = st.selectbox(
        "Eye Contact",
        options         = ["Good", "Average", "Poor"],
        index           = ["Good", "Average", "Poor"].index(obs.get("eye_contact", "Good")),
        label_visibility= "collapsed",
        key             = "sel_eye",
    )

    st.markdown("<br/>", unsafe_allow_html=True)

    # Lip Sync
    st.markdown("<div class='obs-card'><div class='obs-icon'>🎙️</div><div class='obs-label'>Lip Sync</div></div>", unsafe_allow_html=True)
    lip_sync = st.selectbox(
        "Lip Sync",
        options         = ["Matched", "Slight Delay", "Large Delay"],
        index           = ["Matched", "Slight Delay", "Large Delay"].index(obs.get("lip_sync", "Matched")),
        label_visibility= "collapsed",
        key             = "sel_lip",
    )

    st.markdown("<br/>", unsafe_allow_html=True)

    # Voice Behaviour
    st.markdown("<div class='obs-card'><div class='obs-icon'>🔊</div><div class='obs-label'>Voice Behaviour</div></div>", unsafe_allow_html=True)
    voice = st.selectbox(
        "Voice Behaviour",
        options         = ["Natural", "Delayed", "Robotic"],
        index           = ["Natural", "Delayed", "Robotic"].index(obs.get("voice_behaviour", "Natural")),
        label_visibility= "collapsed",
        key             = "sel_voice",
    )

    st.markdown("<br/>", unsafe_allow_html=True)

    # Prompting Detected
    st.markdown("<div class='obs-card'><div class='obs-icon'>📋</div><div class='obs-label'>Prompting Detected</div></div>", unsafe_allow_html=True)
    prompting = st.selectbox(
        "Prompting Detected",
        options         = ["No", "Yes"],
        index           = ["No", "Yes"].index(obs.get("prompting_detected", "No")),
        label_visibility= "collapsed",
        key             = "sel_prompt",
    )

    # Update behavioral obs in session state
    st.session_state.behavioral_obs = {
        "eye_contact":        eye_contact,
        "lip_sync":           lip_sync,
        "voice_behaviour":    voice,
        "prompting_detected": prompting,
    }

    # ── Observation Risk Preview ───────────────────────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    behavioral_risk_pts = 0
    if eye_contact  == "Poor":          behavioral_risk_pts += 15
    elif eye_contact == "Average":       behavioral_risk_pts += 7
    if lip_sync     == "Large Delay":   behavioral_risk_pts += 20
    elif lip_sync   == "Slight Delay":  behavioral_risk_pts += 10
    if voice        == "Robotic":       behavioral_risk_pts += 10
    elif voice      == "Delayed":       behavioral_risk_pts += 5
    if prompting    == "Yes":           behavioral_risk_pts += 15

    beh_color = "#ef4444" if behavioral_risk_pts >= 30 else ("#f59e0b" if behavioral_risk_pts >= 10 else "#10b981")
    st.markdown(
        f"""<div style='background:#131929; border:1px solid rgba(255,255,255,0.06);
                       border-radius:8px; padding:12px; text-align:center;'>
            <div style='color:#94a3b8; font-size:0.78rem; margin-bottom:4px;'>
                Behavioral Risk Points
            </div>
            <div style='color:{beh_color}; font-size:1.6rem; font-weight:700;'>
                +{behavioral_risk_pts}
            </div>
            <div style='color:#475569; font-size:0.72rem;'>out of 60 max</div>
        </div>""",
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# ANALYZE BUTTON
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<br/>", unsafe_allow_html=True)
st.markdown("---")

btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
with btn_col2:
    analyze_disabled = not (question.strip() and answer.strip())
    analyze_btn      = st.button(
        "🤖 Run AI Analysis",
        use_container_width = True,
        disabled            = analyze_disabled,
        type                = "primary",
    )

if analyze_disabled and not (question.strip() and answer.strip()):
    st.markdown(
        "<div style='text-align:center; color:#64748b; font-size:0.85rem;'>"
        "Please fill in both the Interview Question and Candidate Answer to proceed."
        "</div>",
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# ANALYSIS EXECUTION
# ─────────────────────────────────────────────────────────────────────────────
if analyze_btn:
    with st.spinner("🤖 Gemini 2.5 Flash is analyzing the interview..."):
        analysis = analyze_interview(
            resume_text      = st.session_state.resume_text,
            question         = question,
            answer           = answer,
            transcript_notes = notes,
            api_key          = st.session_state.gemini_api_key,
        )
    st.session_state.analysis_result = analysis

    with st.spinner("⚙️ Calculating risk score..."):
        risk = calculate_risk(analysis, st.session_state.behavioral_obs)
    st.session_state.risk_result    = risk
    st.session_state.analysis_complete = True
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# RESULTS SECTION
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.analysis_complete and st.session_state.analysis_result:
    analysis = st.session_state.analysis_result
    risk     = st.session_state.risk_result

    st.markdown("<br/>", unsafe_allow_html=True)

    # ── API Status Banner ─────────────────────────────────────────────────────
    if analysis.get("_api_used"):
        st.success("✅ Analysis powered by **Google Gemini 2.5 Flash**")
    else:
        st.warning("⚠️ Running in **fallback mode** — configure Gemini API key for full AI analysis.")

    st.markdown("""<div class="section-header"><h3>📊 Analysis Results</h3></div>""", unsafe_allow_html=True)

    # ── Metric Cards Row ──────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)

    skill_pct  = analysis.get("skill_match_percentage", 0)
    depth      = analysis.get("technical_depth", "N/A")
    conf_score = analysis.get("confidence_score", 0)
    risk_score = risk.risk_score

    depth_delta_color = "normal" if depth == "Strong" else ("inverse" if depth == "Weak" else "off")

    m1.metric("🎯 Skill Match",         f"{skill_pct}%",    delta=f"{'Low' if skill_pct < 50 else ('Good' if skill_pct >= 70 else 'Medium')}", delta_color="off")
    m2.metric("🔬 Technical Depth",     depth,              delta_color=depth_delta_color)
    m3.metric("💡 Confidence Score",    f"{conf_score}%",   delta_color="off")
    m4.metric(f"{risk.risk_emoji} Risk Score", f"{risk_score}/100", delta=risk.risk_level, delta_color="off")

    st.markdown("<br/>", unsafe_allow_html=True)

    # ── Results Grid: Gauge + Factors ─────────────────────────────────────────
    gauge_col, factors_col = st.columns([1, 1], gap="large")

    with gauge_col:
        # Plotly Gauge
        color = risk.risk_color
        fig = go.Figure(go.Indicator(
            mode   = "gauge+number",
            value  = risk_score,
            domain = {"x": [0, 1], "y": [0, 1]},
            title  = {
                "text": f"<b>Risk Score</b><br><span style='font-size:0.9em; color:{color};'>{risk.risk_level} RISK</span>",
                "font": {"size": 17, "color": "#f1f5f9"},
            },
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickwidth": 1,
                    "tickcolor": "#475569",
                    "tickfont":  {"color": "#94a3b8", "size": 10},
                },
                "bar":       {"color": color, "thickness": 0.25},
                "bgcolor":   "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0,  30],  "color": "rgba(16,185,129,0.12)"},
                    {"range": [30, 70],  "color": "rgba(245,158,11,0.12)"},
                    {"range": [70, 100], "color": "rgba(239,68,68,0.12)"},
                ],
                "threshold": {
                    "line":      {"color": color, "width": 4},
                    "thickness": 0.75,
                    "value":     risk_score,
                },
            },
            number={"font": {"size": 56, "color": color}, "suffix": "/100"},
        ))
        fig.update_layout(
            paper_bgcolor = "rgba(0,0,0,0)",
            plot_bgcolor  = "rgba(0,0,0,0)",
            font          = {"color": "#f1f5f9", "family": "Inter"},
            height        = 320,
            margin        = {"t": 70, "b": 20, "l": 30, "r": 30},
        )
        st.plotly_chart(fig, use_container_width=True)

        # Risk Level Badge
        badge_class = f"badge-{risk.risk_level.lower()}"
        st.markdown(
            f"<div style='text-align:center; margin-top:-10px;'>"
            f"  <span class='{badge_class}'>{risk.risk_emoji} {risk.risk_level} INTEGRITY RISK</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with factors_col:
        st.markdown("**⚠️ Risk Factors Detected**")
        if not risk.factors:
            st.markdown(
                "<div class='rec-box rec-low'>✅ No significant risk factors detected. "
                "Candidate appears consistent.</div>",
                unsafe_allow_html=True,
            )
        else:
            names, scores, colors = get_factor_chart_data(risk)
            bar_fig = go.Figure(go.Bar(
                x            = scores,
                y            = names,
                orientation  = "h",
                marker_color = colors,
                text         = [f"+{s} pts" for s in scores],
                textposition = "outside",
                textfont     = {"color": "#f1f5f9", "size": 11},
            ))
            bar_fig.update_layout(
                paper_bgcolor = "rgba(0,0,0,0)",
                plot_bgcolor  = "rgba(17,24,39,0.6)",
                font          = {"color": "#f1f5f9", "family": "Inter"},
                height        = max(220, len(names) * 48 + 40),
                margin        = {"t": 10, "b": 10, "l": 10, "r": 60},
                xaxis = {
                    "color": "#475569", "gridcolor": "rgba(255,255,255,0.05)",
                    "range": [0, max(scores) * 1.35],
                },
                yaxis = {
                    "color": "#94a3b8", "tickfont": {"size": 10},
                    "automargin": True,
                },
                bargap = 0.3,
            )
            st.plotly_chart(bar_fig, use_container_width=True)

        # Skill match progress bar
        st.markdown("**🎯 Skill Match Breakdown**")
        st.progress(skill_pct / 100)
        st.markdown(
            f"<div style='color:#94a3b8; font-size:0.78rem;'>{skill_pct}% match between resume claims and interview response</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<br/>", unsafe_allow_html=True)

    # ── Detail Expanders ──────────────────────────────────────────────────────
    exp1, exp2, exp3 = st.columns(3)

    with exp1:
        with st.expander("✅ Resume Claims Verified"):
            verified = analysis.get("resume_claims_verified", [])
            if verified:
                for v in verified:
                    st.markdown(f"<div style='color:#6ee7b7; font-size:0.85rem; margin-bottom:6px;'>✓ {v}</div>", unsafe_allow_html=True)
            else:
                st.caption("No claims verified by the interview response.")

    with exp2:
        with st.expander("❌ Claims Unverified"):
            unverified = analysis.get("resume_claims_unverified", [])
            if unverified:
                for u in unverified:
                    st.markdown(f"<div style='color:#fca5a5; font-size:0.85rem; margin-bottom:6px;'>✗ {u}</div>", unsafe_allow_html=True)
            else:
                st.caption("All resume claims appear consistent.")

    with exp3:
        with st.expander("🔍 Missing Skills"):
            missing = analysis.get("missing_skills", [])
            if missing:
                for m in missing:
                    st.markdown(f"<div style='color:#fcd34d; font-size:0.85rem; margin-bottom:6px;'>⚠ {m}</div>", unsafe_allow_html=True)
            else:
                st.caption("No missing skills identified.")

    # ── Key Observations ──────────────────────────────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    with st.expander("📋 AI Key Observations", expanded=True):
        observations = analysis.get("key_observations", [])
        for obs in observations:
            st.markdown(f"<div style='color:#c4b5fd; font-size:0.88rem; padding:4px 0;'>• {obs}</div>", unsafe_allow_html=True)

    # ── AI Explanation ────────────────────────────────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("**🤖 AI Assessment Explanation**")
    st.markdown(
        f"<div class='ai-explanation'>{analysis.get('ai_explanation', 'No explanation available.')}</div>",
        unsafe_allow_html=True,
    )

    # ── Recommendation ────────────────────────────────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("**📋 Recruiter Recommendation**")
    rec_class = f"rec-{risk.risk_level.lower()}"
    st.markdown(
        f"<div class='rec-box {rec_class}'>{risk.recommendation}</div>",
        unsafe_allow_html=True,
    )

    # ── Summary Line ──────────────────────────────────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='info-box'><b>Summary:</b> {risk.summary_line}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# Navigation Footer
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
nav1, nav2, nav3 = st.columns([1, 2, 1])

with nav1:
    if st.button("← Back to Candidate Profile", use_container_width=True):
        st.switch_page("pages/1_Candidate_Profile.py")

with nav3:
    if st.button(
        "📄 View & Download Report →",
        use_container_width = True,
        disabled            = not st.session_state.analysis_complete,
        type                = "primary",
    ):
        st.switch_page("pages/3_Report.py")
