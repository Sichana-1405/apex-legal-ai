"""
pages/1_Candidate_Profile.py
─────────────────────────────
Step 1 of 3 — Candidate Profile & Resume Loading.

Users can:
  • Browse and select one of 5 synthetic sample candidate cards
  • OR upload their own PDF / TXT resume file

Selected resume text and candidate name are stored in session state
for downstream use in the Interview Analysis page.
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title = "Candidate Profile — Interview Integrity Analyzer",
    page_icon  = "📄",
    layout     = "wide",
)

from utils.styles          import get_css, sidebar_branding, step_indicator
from utils.sample_candidates import SAMPLE_CANDIDATES
from utils.resume_parser   import parse_uploaded_file

st.markdown(get_css(), unsafe_allow_html=True)

# ── Ensure session state keys exist ───────────────────────────────────────────
if "resume_text"        not in st.session_state: st.session_state.resume_text        = ""
if "candidate_name"     not in st.session_state: st.session_state.candidate_name     = ""
if "selected_candidate" not in st.session_state: st.session_state.selected_candidate = None
if "gemini_api_key"     not in st.session_state: st.session_state.gemini_api_key     = ""
if "analysis_complete"  not in st.session_state: st.session_state.analysis_complete  = False

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(sidebar_branding(), unsafe_allow_html=True)
    api_key_input = st.text_input(
        "Gemini API Key",
        value       = st.session_state.gemini_api_key,
        type        = "password",
        placeholder = "AIza...",
    )
    if api_key_input:
        st.session_state.gemini_api_key = api_key_input
    st.markdown("<hr/>", unsafe_allow_html=True)
    if st.session_state.candidate_name:
        st.success(f"Loaded: **{st.session_state.candidate_name}**")
    else:
        st.info("No candidate loaded yet.")

# ── Step Indicator ────────────────────────────────────────────────────────────
st.markdown(step_indicator(1), unsafe_allow_html=True)
st.markdown("---")

# ── Page Header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="section-header">
  <h3>📄 Candidate Profile</h3>
  <p>Select a sample candidate or upload a resume to begin the analysis.</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Tab Layout — Sample vs Upload
# ─────────────────────────────────────────────────────────────────────────────
tab_sample, tab_upload = st.tabs(["👥 Sample Candidates", "📤 Upload Resume"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: Sample Candidates
# ═══════════════════════════════════════════════════════════════════════════════
with tab_sample:
    st.markdown(
        "<p style='color:#94a3b8; font-size:0.88rem; margin-bottom:18px;'>"
        "Click a candidate card to load their profile. All profiles are completely synthetic.</p>",
        unsafe_allow_html=True,
    )

    # Render candidate cards in a 3+2 grid
    row1 = st.columns(3)
    row2 = st.columns(3)
    all_cols = row1 + row2

    for idx, candidate in enumerate(SAMPLE_CANDIDATES):
        with all_cols[idx]:
            is_selected = (
                st.session_state.selected_candidate is not None and
                st.session_state.selected_candidate.get("id") == candidate["id"]
            )
            border_style = "border: 2px solid #3b82f6 !important;" if is_selected else ""

            st.markdown(
                f"""<div class="candidate-card" style="{border_style}">
                    <div style="font-size:2rem; margin-bottom:8px;">{candidate['avatar']}</div>
                    <div class="candidate-name">{candidate['name']}</div>
                    <div class="candidate-role">{candidate['role']}</div>
                    <div class="candidate-exp">Experience: {candidate['experience']}</div>
                    <div style="margin-top:8px; font-size:0.75rem; color:#64748b;">
                        {candidate['skills_summary']}
                    </div>
                    <div style="margin-top:10px; font-size:0.72rem; color:#475569; font-style:italic;">
                        📍 {candidate['education']}
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

            btn_label = "✓ Selected" if is_selected else "Select Candidate"
            btn_key   = f"select_{candidate['id']}"

            if st.button(btn_label, key=btn_key, use_container_width=True):
                st.session_state.selected_candidate = candidate
                st.session_state.resume_text        = candidate["resume_text"].strip()
                st.session_state.candidate_name     = candidate["name"]
                st.session_state.analysis_complete  = False
                st.session_state.analysis_result    = None
                st.session_state.risk_result        = None
                st.rerun()

    # ── Selected Preview ──────────────────────────────────────────────────────
    if st.session_state.selected_candidate:
        st.markdown("---")
        sel = st.session_state.selected_candidate
        st.markdown(
            f"""<div style='background:#1a2035; border:1px solid rgba(59,130,246,0.3);
                         border-radius:12px; padding:18px; margin-top:12px;'>
                <div style='font-size:1rem; font-weight:700; color:#f1f5f9; margin-bottom:6px;'>
                    {sel['avatar']} {sel['name']} — <span style='color:#60a5fa;'>{sel['role']}</span>
                </div>
                <div style='font-size:0.82rem; color:#94a3b8;'>
                    {sel['experience']} Experience &nbsp;|&nbsp; {sel['education']}
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
        with st.expander("📄 View Resume Text", expanded=False):
            st.text(st.session_state.resume_text)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: Upload Resume
# ═══════════════════════════════════════════════════════════════════════════════
with tab_upload:
    st.markdown(
        "<p style='color:#94a3b8; font-size:0.88rem; margin-bottom:14px;'>"
        "Upload a PDF or TXT resume file. Text will be extracted automatically.</p>",
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Drop resume here or click to browse",
        type    = ["pdf", "txt"],
        help    = "Supported formats: PDF, TXT. Max file size: 5 MB.",
        label_visibility = "collapsed",
    )

    override_name = st.text_input(
        "Candidate Name (optional override)",
        placeholder = "Auto-detected from resume — enter to override",
    )

    if uploaded_file:
        with st.spinner("Parsing resume..."):
            resume_text, detected_name = parse_uploaded_file(uploaded_file)

        if resume_text.startswith("⚠️"):
            st.error(resume_text)
        else:
            final_name = override_name.strip() or detected_name

            if st.button("✅ Use This Resume", use_container_width=True):
                st.session_state.resume_text        = resume_text
                st.session_state.candidate_name     = final_name
                st.session_state.selected_candidate = {
                    "id":            99,
                    "name":          final_name,
                    "role":          "Uploaded Resume",
                    "experience":    "Unknown",
                    "avatar":        "📤",
                    "skills_summary":"See resume",
                    "education":     "See resume",
                    "resume_text":   resume_text,
                }
                st.session_state.analysis_complete  = False
                st.session_state.analysis_result    = None
                st.session_state.risk_result        = None
                st.success(f"✅ Resume loaded for: **{final_name}**")
                st.rerun()

            # Preview
            with st.expander("📄 Preview Extracted Text", expanded=True):
                st.text(resume_text[:2000] + (" [truncated...]" if len(resume_text) > 2000 else ""))

# ─────────────────────────────────────────────────────────────────────────────
# Navigation Footer
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])

with nav_col1:
    if st.button("🏠 Back to Home", use_container_width=True):
        st.switch_page("app.py")

with nav_col3:
    resume_loaded = bool(st.session_state.resume_text)
    if st.button(
        "🔍 Proceed to Interview Analysis →",
        use_container_width = True,
        disabled            = not resume_loaded,
        type                = "primary",
    ):
        st.switch_page("pages/2_Interview_Analysis.py")

if not resume_loaded:
    st.markdown(
        "<div class='info-box' style='margin-top:8px; text-align:center;'>"
        "⬆️ Please select a sample candidate or upload a resume to continue."
        "</div>",
        unsafe_allow_html=True,
    )
