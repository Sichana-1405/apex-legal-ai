"""
pages/3_Report.py
──────────────────
Step 3 of 3 — Full Analysis Summary & PDF Report Download.

Displays a complete formatted summary of the interview integrity assessment
and provides a one-click downloadable PDF report for recruiter records.
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title = "Report — Interview Integrity Analyzer",
    page_icon  = "📄",
    layout     = "wide",
)

import plotly.graph_objects as go
from datetime               import datetime
from utils.styles           import get_css, sidebar_branding, step_indicator
from utils.report_generator import generate_pdf_report
from models.risk_engine     import get_factor_chart_data

st.markdown(get_css(), unsafe_allow_html=True)

# ── Ensure session state keys ─────────────────────────────────────────────────
for key, default in [
    ("resume_text",        ""),
    ("candidate_name",     ""),
    ("selected_candidate", None),
    ("interview_question", ""),
    ("candidate_answer",   ""),
    ("transcript_notes",   ""),
    ("behavioral_obs",     {"eye_contact":"Good","lip_sync":"Matched","voice_behaviour":"Natural","prompting_detected":"No"}),
    ("analysis_result",    None),
    ("risk_result",        None),
    ("analysis_complete",  False),
    ("gemini_api_key",     ""),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(sidebar_branding(), unsafe_allow_html=True)
    st.markdown("<hr/>", unsafe_allow_html=True)
    if st.session_state.candidate_name:
        st.success(f"Candidate: **{st.session_state.candidate_name}**")
    if st.session_state.analysis_complete and st.session_state.risk_result:
        risk  = st.session_state.risk_result
        level = risk.risk_level
        score = risk.risk_score
        emoji = {"LOW":"🟢","MEDIUM":"🟡","HIGH":"🔴"}.get(level,"⚪")
        st.markdown(
            f"<div style='color:#94a3b8;font-size:0.82rem;'>"
            f"Risk: <b style='color:#f1f5f9;'>{emoji} {level} ({score}/100)</b></div>",
            unsafe_allow_html=True,
        )
    st.markdown("<hr/>", unsafe_allow_html=True)
    if st.button("🔄 Start New Analysis", use_container_width=True):
        for k in ["resume_text","candidate_name","selected_candidate","interview_question",
                  "candidate_answer","transcript_notes","analysis_result","risk_result","analysis_complete"]:
            st.session_state[k] = "" if isinstance(st.session_state.get(k,""), str) else None
        st.session_state.analysis_complete = False
        st.switch_page("pages/1_Candidate_Profile.py")

# ── Step Indicator ────────────────────────────────────────────────────────────
st.markdown(step_indicator(3), unsafe_allow_html=True)
st.markdown("---")

# ── Guard: analysis must be complete ─────────────────────────────────────────
if not st.session_state.analysis_complete or not st.session_state.risk_result:
    st.warning("⚠️ No analysis found. Please complete Step 2 first.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Go to Candidate Profile"):
            st.switch_page("pages/1_Candidate_Profile.py")
    with col2:
        if st.button("← Go to Interview Analysis"):
            st.switch_page("pages/2_Interview_Analysis.py")
    st.stop()

# ── Load session data ─────────────────────────────────────────────────────────
name     = st.session_state.candidate_name
analysis = st.session_state.analysis_result
risk     = st.session_state.risk_result
obs      = st.session_state.behavioral_obs
question = st.session_state.interview_question
answer   = st.session_state.candidate_answer
notes    = st.session_state.transcript_notes
resume   = st.session_state.resume_text
sel      = st.session_state.selected_candidate or {}

# ─────────────────────────────────────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────────────────────────────────────
risk_color = risk.risk_color
risk_level = risk.risk_level
risk_score = risk.risk_score
risk_emoji = risk.risk_emoji

st.markdown(f"""
<div style="background: linear-gradient(135deg, rgba(59,130,246,0.08), rgba(139,92,246,0.08));
            border: 1px solid rgba(59,130,246,0.2); border-radius:16px; padding:28px 32px; margin-bottom:24px;">
    <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:16px;">
        <div>
            <div style="font-size:1.8rem; font-weight:800; color:#f1f5f9;">{name}</div>
            <div style="color:#60a5fa; font-size:0.95rem; margin-top:4px;">
                {sel.get('role','') or 'Interview Candidate'} &nbsp;•&nbsp; {sel.get('experience','') or ''}
            </div>
            <div style="color:#64748b; font-size:0.8rem; margin-top:6px;">
                📅 Report generated: {datetime.now().strftime('%d %B %Y at %H:%M')}
            </div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:3.5rem; font-weight:800; color:{risk_color}; line-height:1;">{risk_score}</div>
            <div style="color:{risk_color}; font-size:0.9rem; font-weight:600;">/100 Risk Score</div>
            <div style="margin-top:8px;">
                <span class="badge-{risk_level.lower()}">{risk_emoji} {risk_level} RISK</span>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── PDF Download Button ───────────────────────────────────────────────────────
with st.spinner("📄 Generating PDF report..."):
    # Serialize risk_result factors to dicts for report generator
    risk_dict = {
        "risk_score":     risk.risk_score,
        "risk_level":     risk.risk_level,
        "risk_color":     risk.risk_color,
        "risk_emoji":     risk.risk_emoji,
        "recommendation": risk.recommendation,
        "summary_line":   risk.summary_line,
        "factors": [
            {
                "name":        f.name,
                "score":       f.score,
                "description": f.description,
                "category":    f.category,
                "severity":    f.severity,
            }
            for f in risk.factors
        ],
    }
    pdf_bytes = generate_pdf_report(
        candidate_name   = name,
        resume_text      = resume,
        question         = question,
        answer           = answer,
        transcript_notes = notes,
        behavioral_obs   = obs,
        analysis_result  = analysis,
        risk_result      = risk_dict,
    )

dl_col1, dl_col2, dl_col3 = st.columns([1, 2, 1])
with dl_col2:
    filename = f"interview_integrity_{name.replace(' ','_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    st.download_button(
        label            = "⬇️ Download PDF Report",
        data             = pdf_bytes,
        file_name        = filename,
        mime             = "application/pdf",
        use_container_width = True,
        type             = "primary",
    )

st.markdown("<br/>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FULL REPORT BODY
# ─────────────────────────────────────────────────────────────────────────────
rep_col, side_col = st.columns([3, 2], gap="large")

# ════════════════════════════════════════════════════════════════════════════
# LEFT COLUMN — Detailed Report
# ════════════════════════════════════════════════════════════════════════════
with rep_col:

    # ── Section 1: Resume Summary ─────────────────────────────────────────
    st.markdown("""<div class="section-header"><h3>📄 Resume Summary</h3></div>""", unsafe_allow_html=True)

    r1, r2 = st.columns(2)
    with r1:
        st.markdown(f"""
        <div style="background:#1a2035; border-radius:10px; padding:14px; border:1px solid rgba(59,130,246,0.2);">
            <div style="color:#94a3b8; font-size:0.75rem; margin-bottom:4px;">CANDIDATE</div>
            <div style="color:#f1f5f9; font-weight:700;">{name}</div>
        </div>""", unsafe_allow_html=True)
    with r2:
        st.markdown(f"""
        <div style="background:#1a2035; border-radius:10px; padding:14px; border:1px solid rgba(59,130,246,0.2);">
            <div style="color:#94a3b8; font-size:0.75rem; margin-bottom:4px;">ROLE APPLIED</div>
            <div style="color:#f1f5f9; font-weight:700;">{sel.get('role','N/A')}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    with st.expander("📋 Full Resume Text", expanded=False):
        st.text(resume[:3000] + (" [truncated...]" if len(resume) > 3000 else ""))

    # ── Section 2: Interview Details ──────────────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("""<div class="section-header"><h3>💬 Interview Details</h3></div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:#1a2035; border-radius:10px; padding:16px; border:1px solid rgba(59,130,246,0.2); margin-bottom:12px;">
        <div style="color:#94a3b8; font-size:0.75rem; margin-bottom:6px;">INTERVIEW QUESTION</div>
        <div style="color:#f1f5f9; font-size:0.92rem; line-height:1.6;">{question or '—'}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:#1a2035; border-radius:10px; padding:16px; border:1px solid rgba(59,130,246,0.2); margin-bottom:12px;">
        <div style="color:#94a3b8; font-size:0.75rem; margin-bottom:6px;">CANDIDATE'S ANSWER</div>
        <div style="color:#f1f5f9; font-size:0.88rem; line-height:1.7; white-space:pre-wrap;">{(answer or '—')[:1000]}{'...' if len(answer or '') > 1000 else ''}</div>
    </div>""", unsafe_allow_html=True)

    if notes:
        st.markdown(f"""
        <div style="background:#131929; border-radius:10px; padding:14px; border:1px solid rgba(255,255,255,0.06);">
            <div style="color:#94a3b8; font-size:0.75rem; margin-bottom:6px;">TRANSCRIPT NOTES</div>
            <div style="color:#c4b5fd; font-size:0.85rem; font-style:italic;">{notes}</div>
        </div>""", unsafe_allow_html=True)

    # ── Section 3: Behavioral Observations ───────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("""<div class="section-header"><h3>👁️ Behavioral Observations</h3></div>""", unsafe_allow_html=True)

    obs_icons = {"Good":"🟢","Average":"🟡","Poor":"🔴",
                 "Matched":"🟢","Slight Delay":"🟡","Large Delay":"🔴",
                 "Natural":"🟢","Delayed":"🟡","Robotic":"🔴",
                 "No":"🟢","Yes":"🔴"}

    b1, b2, b3, b4 = st.columns(4)
    for col, (label, key) in zip(
        [b1, b2, b3, b4],
        [("Eye Contact","eye_contact"), ("Lip Sync","lip_sync"),
         ("Voice","voice_behaviour"), ("Prompting","prompting_detected")]
    ):
        val = obs.get(key, "N/A")
        icon = obs_icons.get(val, "⚪")
        with col:
            st.markdown(f"""
            <div style="background:#1a2035; border-radius:10px; padding:14px; text-align:center;
                        border:1px solid rgba(59,130,246,0.15);">
                <div style="font-size:1.4rem;">{icon}</div>
                <div style="color:#94a3b8; font-size:0.72rem; margin:4px 0;">{label}</div>
                <div style="color:#f1f5f9; font-size:0.85rem; font-weight:600;">{val}</div>
            </div>""", unsafe_allow_html=True)

    # ── Section 4: AI Analysis ────────────────────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("""<div class="section-header"><h3>🤖 AI Analysis (Gemini 2.5 Flash)</h3></div>""", unsafe_allow_html=True)

    api_used = analysis.get("_api_used", False)
    st.markdown(
        f"<div style='color:{'#10b981' if api_used else '#f59e0b'}; font-size:0.82rem; margin-bottom:12px;'>"
        f"{'✅ Powered by Google Gemini 2.5 Flash' if api_used else '⚠️ Fallback mode — Gemini API not used'}</div>",
        unsafe_allow_html=True,
    )

    a1, a2, a3 = st.columns(3)
    skill_pct  = analysis.get("skill_match_percentage", 0)
    depth      = analysis.get("technical_depth", "N/A")
    conf       = analysis.get("confidence_score", 0)

    depth_color = {"Strong":"#10b981","Moderate":"#f59e0b","Weak":"#ef4444"}.get(depth,"#94a3b8")

    for col, (label, val, color) in zip(
        [a1, a2, a3],
        [
            ("Skill Match",       f"{skill_pct}%", "#3b82f6"),
            ("Technical Depth",   depth,           depth_color),
            ("Confidence Score",  f"{conf}%",      "#8b5cf6"),
        ]
    ):
        with col:
            st.markdown(f"""
            <div style="background:#1a2035; border-radius:10px; padding:16px; text-align:center;
                        border:1px solid rgba(59,130,246,0.15);">
                <div style="color:{color}; font-size:1.6rem; font-weight:800;">{val}</div>
                <div style="color:#94a3b8; font-size:0.78rem; margin-top:4px;">{label}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Verified / Unverified
    vcol, uvcol = st.columns(2)
    with vcol:
        verified = analysis.get("resume_claims_verified", [])
        st.markdown("**✅ Claims Verified**")
        for v in (verified[:4] or ["None identified"]):
            st.markdown(f"<div style='color:#6ee7b7; font-size:0.83rem; padding:2px 0;'>✓ {v}</div>", unsafe_allow_html=True)
    with uvcol:
        unverified = analysis.get("resume_claims_unverified", [])
        st.markdown("**❌ Claims Unverified**")
        for u in (unverified[:4] or ["None identified"]):
            st.markdown(f"<div style='color:#fca5a5; font-size:0.83rem; padding:2px 0;'>✗ {u}</div>", unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    missing = analysis.get("missing_skills", [])
    if missing:
        st.markdown("**⚠️ Missing Skills**")
        chips = " ".join(
            f"<span style='background:rgba(245,158,11,0.15); border:1px solid rgba(245,158,11,0.3); "
            f"color:#fcd34d; border-radius:999px; padding:3px 12px; font-size:0.78rem; margin:2px; display:inline-block;'>"
            f"{m}</span>"
            for m in missing[:8]
        )
        st.markdown(chips, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("**🤖 AI Explanation**")
    st.markdown(
        f"<div class='ai-explanation'>{analysis.get('ai_explanation','No explanation available.')}</div>",
        unsafe_allow_html=True,
    )

    # ── Section 5: Recommendation ─────────────────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("""<div class="section-header"><h3>📋 Recommendation</h3></div>""", unsafe_allow_html=True)
    rec_class = f"rec-{risk_level.lower()}"
    st.markdown(
        f"<div class='rec-box {rec_class}'>{risk.recommendation}</div>",
        unsafe_allow_html=True,
    )

    # ── Disclaimer ────────────────────────────────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:rgba(239,68,68,0.06); border:1px solid rgba(239,68,68,0.25);
                border-radius:10px; padding:14px 18px; font-size:0.78rem; color:#94a3b8; line-height:1.7;">
        <b style="color:#fca5a5;">⚖️ Important Disclaimer</b><br/>
        This report is generated by an AI-assisted <i>prototype decision-support tool</i> and is intended 
        solely to assist human recruiters in identifying potential inconsistencies in interview responses. 
        It does <b>NOT</b> make hiring decisions, constitute professional HR advice, or guarantee accuracy. 
        All risk assessments must be reviewed by a qualified human recruiter. No candidate should be 
        rejected based solely on this automated output. This tool does not perform real deepfake 
        detection, facial recognition, or voice biometric analysis.
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# RIGHT COLUMN — Risk Dashboard Summary
# ════════════════════════════════════════════════════════════════════════════
with side_col:

    # ── Mini Gauge ────────────────────────────────────────────────────────
    st.markdown("**📊 Risk Dashboard**")
    mini_gauge = go.Figure(go.Indicator(
        mode   = "gauge+number",
        value  = risk_score,
        domain = {"x": [0, 1], "y": [0, 1]},
        gauge  = {
            "axis":        {"range": [0, 100], "tickfont": {"color":"#94a3b8","size":9}},
            "bar":         {"color": risk_color, "thickness": 0.25},
            "bgcolor":     "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range":[0,30],   "color":"rgba(16,185,129,0.12)"},
                {"range":[30,70],  "color":"rgba(245,158,11,0.12)"},
                {"range":[70,100], "color":"rgba(239,68,68,0.12)"},
            ],
            "threshold": {"line":{"color":risk_color,"width":3}, "thickness":0.75, "value":risk_score},
        },
        number = {"font":{"size":44,"color":risk_color}, "suffix":"/100"},
    ))
    mini_gauge.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor ="rgba(0,0,0,0)",
        font         ={"color":"#f1f5f9"},
        height       =250,
        margin       ={"t":40,"b":10,"l":20,"r":20},
    )
    st.plotly_chart(mini_gauge, use_container_width=True)

    st.markdown(
        f"<div style='text-align:center; margin-top:-12px; margin-bottom:16px;'>"
        f"<span class='badge-{risk_level.lower()}'>{risk_emoji} {risk_level} INTEGRITY RISK</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Risk Factors List ─────────────────────────────────────────────────
    st.markdown("**⚠️ Risk Factors**")
    if not risk.factors:
        st.markdown(
            "<div style='color:#6ee7b7; font-size:0.85rem; padding:10px; "
            "background:rgba(16,185,129,0.1); border-radius:8px;'>"
            "✅ No risk factors detected.</div>",
            unsafe_allow_html=True,
        )
    else:
        for f in sorted(risk.factors, key=lambda x: x.score, reverse=True):
            sev_color = {"high":"#ef4444","medium":"#f59e0b","low":"#3b82f6"}.get(f.severity,"#94a3b8")
            st.markdown(f"""
            <div class="factor-row">
                <div>
                    <div class="factor-name">{f.name}</div>
                    <div class="factor-desc">{f.description[:60]}...</div>
                </div>
                <div class="factor-score" style="color:{sev_color};">+{f.score}</div>
            </div>""", unsafe_allow_html=True)

    # ── Score Breakdown Pie ───────────────────────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    if risk.factors:
        ai_pts  = sum(f.score for f in risk.factors if f.category == "AI Analysis")
        beh_pts = sum(f.score for f in risk.factors if f.category == "Behavioral")
        if ai_pts + beh_pts > 0:
            pie = go.Figure(go.Pie(
                labels    = ["AI Analysis", "Behavioral"],
                values    = [ai_pts, beh_pts],
                hole      = 0.55,
                marker    = {"colors": ["#3b82f6","#ef4444"]},
                textinfo  = "label+percent",
                textfont  = {"color":"#f1f5f9","size":10},
            ))
            pie.update_layout(
                paper_bgcolor = "rgba(0,0,0,0)",
                plot_bgcolor  = "rgba(0,0,0,0)",
                font          = {"color":"#f1f5f9"},
                height        = 220,
                margin        = {"t":10,"b":10,"l":10,"r":10},
                showlegend    = False,
            )
            st.markdown("**📉 Score Composition**")
            st.plotly_chart(pie, use_container_width=True)

    # ── Quick Stats ───────────────────────────────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("**📋 Quick Stats**")
    stats = [
        ("Skill Match",    f"{analysis.get('skill_match_percentage',0)}%"),
        ("Tech Depth",     analysis.get("technical_depth","N/A")),
        ("Confidence",     f"{analysis.get('confidence_score',0)}%"),
        ("Risk Factors",   str(len(risk.factors))),
        ("Eye Contact",    obs.get("eye_contact","N/A")),
        ("Lip Sync",       obs.get("lip_sync","N/A")),
        ("Voice",          obs.get("voice_behaviour","N/A")),
        ("Prompting",      obs.get("prompting_detected","N/A")),
    ]
    for label, val in stats:
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center;
                    padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.04);">
            <span style="color:#64748b; font-size:0.78rem;">{label}</span>
            <span style="color:#f1f5f9; font-size:0.82rem; font-weight:600;">{val}</span>
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Navigation Footer
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<br/>", unsafe_allow_html=True)
st.markdown("---")
n1, n2, n3 = st.columns([1, 2, 1])

with n1:
    if st.button("← Back to Analysis", use_container_width=True):
        st.switch_page("pages/2_Interview_Analysis.py")

with n2:
    st.markdown(
        f"<div style='text-align:center; color:#64748b; font-size:0.82rem; padding-top:8px;'>"
        f"📄 {filename if 'filename' in dir() else 'report'} — ready to download above</div>",
        unsafe_allow_html=True,
    )

with n3:
    if st.button("🔄 New Analysis", use_container_width=True):
        for k in ["resume_text","candidate_name","selected_candidate","interview_question",
                  "candidate_answer","transcript_notes","analysis_result","risk_result"]:
            if k in st.session_state:
                st.session_state[k] = None if k in ["selected_candidate","analysis_result","risk_result"] else ""
        st.session_state.analysis_complete = False
        st.switch_page("pages/1_Candidate_Profile.py")
