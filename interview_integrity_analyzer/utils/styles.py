"""
utils/styles.py
───────────────
Shared CSS theme for Interview Integrity Analyzer.
Injected via st.markdown(get_css(), unsafe_allow_html=True) in each page.
"""

def get_css() -> str:
    """Return the full custom CSS string for the dark premium theme."""
    return """
    <style>
    /* ── Google Font ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Root Variables ── */
    :root {
        --bg-primary:    #0a0e1a;
        --bg-secondary:  #111827;
        --bg-card:       #1a2035;
        --bg-card-hover: #1e2647;
        --accent-blue:   #3b82f6;
        --accent-purple: #8b5cf6;
        --accent-cyan:   #06b6d4;
        --success:       #10b981;
        --warning:       #f59e0b;
        --danger:        #ef4444;
        --text-primary:  #f1f5f9;
        --text-secondary:#94a3b8;
        --border:        rgba(59,130,246,0.2);
        --glow-blue:     rgba(59,130,246,0.15);
    }

    /* ── Global Reset ── */
    * { font-family: 'Inter', sans-serif !important; }
    .stApp { background: linear-gradient(160deg, #0a0e1a 0%, #0d1630 50%, #0a0e1a 100%) !important; }
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
    header    { visibility: hidden; }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1225 0%, #111827 100%) !important;
        border-right: 1px solid var(--border) !important;
    }
    section[data-testid="stSidebar"] * { color: var(--text-primary) !important; }
    .st-emotion-cache-pkbazv { color: var(--text-secondary) !important; }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(59,130,246,0.3) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(59,130,246,0.5) !important;
    }

    /* ── Text Inputs / Textareas / Selects ── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {
        background: #1a2035 !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--accent-blue) !important;
        box-shadow: 0 0 0 2px rgba(59,130,246,0.2) !important;
    }

    /* ── Metric Cards ── */
    [data-testid="stMetric"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 16px !important;
    }
    [data-testid="stMetricValue"] { color: var(--text-primary) !important; font-weight: 700 !important; }
    [data-testid="stMetricLabel"] { color: var(--text-secondary) !important; }

    /* ── Expanders ── */
    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
    }
    .streamlit-expanderContent {
        background: #131929 !important;
        border: 1px solid var(--border) !important;
        border-top: none !important;
    }

    /* ── Progress Bar ── */
    .stProgress > div > div > div { border-radius: 999px !important; }
    .stProgress > div > div > div > div { border-radius: 999px !important; }

    /* ── Alerts ── */
    .stAlert { border-radius: 10px !important; }

    /* ── Hero Section ── */
    .hero-container {
        text-align: center;
        padding: 50px 20px 30px 20px;
        background: linear-gradient(135deg, rgba(59,130,246,0.08) 0%, rgba(139,92,246,0.08) 100%);
        border-radius: 20px;
        border: 1px solid var(--border);
        margin-bottom: 30px;
    }
    .hero-title {
        font-size: 3.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 50%, #38bdf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 12px;
        line-height: 1.2;
    }
    .hero-subtitle {
        font-size: 1.15rem;
        color: #94a3b8;
        max-width: 650px;
        margin: 0 auto 20px auto;
        line-height: 1.6;
    }
    .disclaimer-badge {
        display: inline-block;
        background: rgba(239,68,68,0.12);
        border: 1px solid rgba(239,68,68,0.35);
        border-radius: 999px;
        padding: 6px 20px;
        color: #fca5a5;
        font-size: 0.85rem;
        font-weight: 500;
    }

    /* ── Feature Cards ── */
    .feature-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 22px 18px;
        text-align: center;
        transition: all 0.3s ease;
        height: 100%;
    }
    .feature-card:hover {
        border-color: var(--accent-blue);
        box-shadow: 0 0 20px var(--glow-blue);
        transform: translateY(-3px);
    }
    .feature-icon { font-size: 2.2rem; margin-bottom: 10px; }
    .feature-title { font-size: 1rem; font-weight: 700; color: var(--text-primary); margin-bottom: 6px; }
    .feature-desc  { font-size: 0.82rem; color: var(--text-secondary); line-height: 1.5; }

    /* ── Candidate Cards ── */
    .candidate-card {
        background: var(--bg-card);
        border: 2px solid transparent;
        border-radius: 14px;
        padding: 20px;
        cursor: pointer;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .candidate-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
    }
    .candidate-card:hover {
        border-color: var(--accent-blue);
        box-shadow: 0 8px 30px var(--glow-blue);
    }
    .candidate-name { font-size: 1.05rem; font-weight: 700; color: var(--text-primary); }
    .candidate-role { font-size: 0.85rem; color: #60a5fa; font-weight: 500; margin: 3px 0; }
    .candidate-exp  { font-size: 0.8rem;  color: var(--text-secondary); }

    /* ── Risk Badges ── */
    .badge-low    { background:rgba(16,185,129,0.15); border:1px solid rgba(16,185,129,0.4); color:#34d399; border-radius:999px; padding:4px 14px; font-size:0.8rem; font-weight:600; }
    .badge-medium { background:rgba(245,158,11,0.15); border:1px solid rgba(245,158,11,0.4); color:#fbbf24; border-radius:999px; padding:4px 14px; font-size:0.8rem; font-weight:600; }
    .badge-high   { background:rgba(239,68,68,0.15);  border:1px solid rgba(239,68,68,0.4);  color:#f87171; border-radius:999px; padding:4px 14px; font-size:0.8rem; font-weight:600; }

    /* ── Section Headers ── */
    .section-header {
        border-left: 4px solid var(--accent-blue);
        padding-left: 14px;
        margin: 24px 0 16px 0;
    }
    .section-header h3 { color: var(--text-primary); margin:0; font-size:1.15rem; font-weight:700; }
    .section-header p  { color: var(--text-secondary); margin:4px 0 0 0; font-size:0.85rem; }

    /* ── Info Box ── */
    .info-box {
        background: rgba(59,130,246,0.08);
        border: 1px solid rgba(59,130,246,0.25);
        border-radius: 10px;
        padding: 14px 18px;
        color: #93c5fd;
        font-size: 0.88rem;
        line-height: 1.6;
    }

    /* ── Risk Result Panel ── */
    .risk-panel {
        background: var(--bg-card);
        border-radius: 16px;
        padding: 28px;
        border: 1px solid var(--border);
        box-shadow: 0 8px 40px rgba(0,0,0,0.4);
    }
    .risk-score-number {
        font-size: 5rem;
        font-weight: 800;
        line-height: 1;
    }
    .risk-label { font-size: 1rem; font-weight: 500; color: var(--text-secondary); }

    /* ── Step Progress Indicator ── */
    .step-bar {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 16px 0;
        margin-bottom: 10px;
    }
    .step-item {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.82rem;
        font-weight: 500;
    }
    .step-circle {
        width: 26px; height: 26px;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.72rem; font-weight: 700;
    }
    .step-circle.active { background: var(--accent-blue); color: white; }
    .step-circle.done   { background: var(--success);     color: white; }
    .step-circle.idle   { background: #2d3748;            color: #64748b; }
    .step-connector { flex: 1; height: 2px; background: #2d3748; min-width: 20px; }
    .step-connector.done { background: var(--success); }

    /* ── Factor Row ── */
    .factor-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 14px;
        background: #131929;
        border-radius: 8px;
        margin-bottom: 8px;
        border: 1px solid rgba(255,255,255,0.04);
    }
    .factor-name  { font-size:0.88rem; color:var(--text-primary); font-weight:500; }
    .factor-desc  { font-size:0.76rem; color:var(--text-secondary); }
    .factor-score { font-size:1rem; font-weight:700; color:#f87171; }

    /* ── Workflow Steps ── */
    .workflow-step {
        display: flex;
        align-items: flex-start;
        gap: 16px;
        padding: 16px;
        background: var(--bg-card);
        border-radius: 12px;
        border: 1px solid var(--border);
        margin-bottom: 10px;
    }
    .workflow-num {
        min-width: 36px; height: 36px;
        background: linear-gradient(135deg, #3b82f6, #6366f1);
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 0.9rem; color: white;
    }
    .workflow-text h4 { color:var(--text-primary); margin:0 0 4px 0; font-size:0.95rem; }
    .workflow-text p  { color:var(--text-secondary); margin:0; font-size:0.82rem; line-height:1.5; }

    /* ── Upload Zone ── */
    [data-testid="stFileUploader"] {
        background: rgba(59,130,246,0.05) !important;
        border: 2px dashed rgba(59,130,246,0.3) !important;
        border-radius: 12px !important;
    }

    /* ── Divider ── */
    hr { border-color: rgba(255,255,255,0.06) !important; }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-card) !important;
        border-radius: 10px !important;
        padding: 4px !important;
        gap: 4px !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px !important;
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #3b82f6, #6366f1) !important;
        color: white !important;
    }

    /* ── Observation Grid ── */
    .obs-card {
        background: #131929;
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 14px;
        text-align: center;
    }
    .obs-icon  { font-size: 1.6rem; margin-bottom: 6px; }
    .obs-label { font-size: 0.78rem; color: var(--text-secondary); font-weight: 500; }

    /* ── AI Explanation Box ── */
    .ai-explanation {
        background: linear-gradient(135deg, rgba(139,92,246,0.1), rgba(59,130,246,0.1));
        border: 1px solid rgba(139,92,246,0.3);
        border-radius: 12px;
        padding: 20px 24px;
        color: #c4b5fd;
        font-size: 0.95rem;
        line-height: 1.75;
        font-style: italic;
    }

    /* ── Recommendation Box ── */
    .rec-box {
        border-radius: 12px;
        padding: 18px 22px;
        font-size: 0.92rem;
        line-height: 1.6;
        font-weight: 500;
    }
    .rec-low    { background:rgba(16,185,129,0.1);  border:1px solid rgba(16,185,129,0.35); color:#6ee7b7; }
    .rec-medium { background:rgba(245,158,11,0.1);  border:1px solid rgba(245,158,11,0.35); color:#fcd34d; }
    .rec-high   { background:rgba(239,68,68,0.1);   border:1px solid rgba(239,68,68,0.35);  color:#fca5a5; }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #0a0e1a; }
    ::-webkit-scrollbar-thumb { background: #2d3748; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #3b82f6; }
    </style>
    """


def sidebar_branding():
    """Return HTML for the sidebar logo/branding section."""
    return """
    <div style='text-align:center; padding: 16px 8px 24px 8px;'>
        <div style='font-size:2rem; margin-bottom:6px;'>🔍</div>
        <div style='font-size:1.05rem; font-weight:700; color:#f1f5f9;'>Interview Integrity</div>
        <div style='font-size:0.75rem; color:#60a5fa; font-weight:500;'>Analyzer</div>
        <div style='font-size:0.7rem; color:#64748b; margin-top:6px;'>TCS Tech Day Prototype</div>
        <hr style='border-color:rgba(59,130,246,0.2); margin:14px 0;'/>
    </div>
    """


def step_indicator(current_step: int) -> str:
    """
    Returns an HTML progress bar for 3-step workflow.
    current_step: 1, 2, or 3
    """
    steps = [
        ("1", "Candidate Profile"),
        ("2", "Interview Analysis"),
        ("3", "Report"),
    ]
    html = "<div class='step-bar'>"
    for i, (num, label) in enumerate(steps, 1):
        if i < current_step:
            cls = "done"
            icon = "✓"
        elif i == current_step:
            cls = "active"
            icon = num
        else:
            cls = "idle"
            icon = num
        html += f"""
        <div class='step-item'>
            <div class='step-circle {cls}'>{icon}</div>
            <span style='color:{"#f1f5f9" if i == current_step else ("#10b981" if i < current_step else "#475569")}; 
                         font-size:0.8rem; white-space:nowrap;'>{label}</span>
        </div>"""
        if i < 3:
            html += f"<div class='step-connector {'done' if i < current_step else ''}'></div>"
    html += "</div>"
    return html
