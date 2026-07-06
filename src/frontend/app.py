# Main Streamlit entrance script — Apex Legal AI
#
# Single-file frontend that wires together the five-agent ADK pipeline with a
# premium dark-mode interface.  All backend imports are deferred inside the
# run-investigation callback so Streamlit can render the upload form
# immediately without blocking on heavy module initialisation.

import asyncio
import io
import sys
import os
import uuid
import logging
from collections import Counter
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Page configuration — must be the FIRST Streamlit call in the script
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Apex Legal AI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Global CSS — dark premium theme injected once per session
# ---------------------------------------------------------------------------

def _inject_css() -> None:
    """
    Inject global CSS that overrides Streamlit's default light theme with a
    premium dark palette.  Uses CSS variables so colours are consistent across
    all components.
    """
    st.markdown(
        """
        <style>
        /* ── Import Inter font from Google Fonts ── */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        /* ── Root variables ── */
        :root {
            --bg-deep:    #0a0d14;
            --bg-card:    #111827;
            --bg-hover:   #1a2235;
            --border:     #1f2d45;
            --accent:     #3b82f6;
            --accent-glow:#1d4ed8;
            --danger:     #ef4444;
            --warning:    #f59e0b;
            --success:    #10b981;
            --muted:      #6b7280;
            --text:       #e2e8f0;
            --text-dim:   #94a3b8;
            --radius:     12px;
        }

        /* ── Base ── */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif !important;
            background-color: var(--bg-deep) !important;
            color: var(--text) !important;
        }

        /* ── Main container ── */
        .block-container {
            padding: 2rem 3rem !important;
            max-width: 1400px !important;
        }

        /* ── Sidebar ── */
        section[data-testid="stSidebar"] {
            background: var(--bg-card) !important;
            border-right: 1px solid var(--border) !important;
        }
        section[data-testid="stSidebar"] * {
            color: var(--text) !important;
        }

        /* ── Hero banner ── */
        .apex-hero {
            background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 60%, #0f172a 100%);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 2.5rem 3rem;
            margin-bottom: 2rem;
            position: relative;
            overflow: hidden;
        }
        .apex-hero::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(ellipse at 60% 40%, rgba(59,130,246,0.12) 0%, transparent 60%);
            pointer-events: none;
        }
        .apex-hero h1 {
            font-size: 2.4rem !important;
            font-weight: 800 !important;
            background: linear-gradient(90deg, #e2e8f0 30%, #3b82f6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0 0 0.4rem !important;
            letter-spacing: -0.5px;
        }
        .apex-hero p {
            color: var(--text-dim) !important;
            font-size: 1.05rem;
            margin: 0;
            font-weight: 400;
        }
        .apex-badge {
            display: inline-block;
            background: rgba(59,130,246,0.15);
            border: 1px solid rgba(59,130,246,0.4);
            color: #93c5fd;
            font-size: 0.72rem;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: 999px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.9rem;
        }

        /* ── Cards ── */
        .apex-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 1.5rem;
            margin-bottom: 1.2rem;
        }
        .apex-card h3 {
            font-size: 0.8rem !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--text-dim) !important;
            margin: 0 0 0.5rem !important;
        }

        /* ── Metric tiles ── */
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        @media (max-width: 900px) {
            .metric-grid { grid-template-columns: repeat(2, 1fr); }
        }
        .metric-tile {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 1.4rem 1.6rem;
            position: relative;
            overflow: hidden;
            transition: border-color 0.2s;
        }
        .metric-tile:hover { border-color: var(--accent); }
        .metric-tile .mt-label {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--text-dim);
            margin-bottom: 0.5rem;
        }
        .metric-tile .mt-value {
            font-size: 2.1rem;
            font-weight: 800;
            line-height: 1;
            color: var(--text);
        }
        .metric-tile .mt-sub {
            font-size: 0.78rem;
            color: var(--text-dim);
            margin-top: 0.3rem;
        }
        .metric-tile .mt-accent-bar {
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            border-radius: var(--radius) var(--radius) 0 0;
        }
        .accent-blue  { background: var(--accent); }
        .accent-red   { background: var(--danger); }
        .accent-green { background: var(--success); }
        .accent-amber { background: var(--warning); }
        .value-blue   { color: #60a5fa !important; }
        .value-red    { color: #f87171 !important; }
        .value-green  { color: #34d399 !important; }
        .value-amber  { color: #fbbf24 !important; }

        /* ── Pipeline stage tracker ── */
        .stage-tracker {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1.2rem;
            flex-wrap: wrap;
        }
        .stage-pill {
            display: flex;
            align-items: center;
            gap: 0.4rem;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 999px;
            padding: 0.35rem 0.9rem;
            font-size: 0.78rem;
            font-weight: 500;
            color: var(--text-dim);
            transition: all 0.25s;
        }
        .stage-pill.done {
            border-color: var(--success);
            color: #34d399;
            background: rgba(16,185,129,0.08);
        }
        .stage-pill.running {
            border-color: var(--accent);
            color: #93c5fd;
            background: rgba(59,130,246,0.1);
            animation: pulse-border 1.4s ease-in-out infinite;
        }
        .stage-pill.failed {
            border-color: var(--danger);
            color: #f87171;
            background: rgba(239,68,68,0.08);
        }
        @keyframes pulse-border {
            0%, 100% { box-shadow: 0 0 0 0 rgba(59,130,246,0.3); }
            50%       { box-shadow: 0 0 0 4px rgba(59,130,246,0.0); }
        }

        /* ── Divider ── */
        .apex-divider {
            border: none;
            border-top: 1px solid var(--border);
            margin: 1.5rem 0;
        }

        /* ── Upload zone ── */
        [data-testid="stFileUploader"] {
            background: var(--bg-card) !important;
            border: 2px dashed var(--border) !important;
            border-radius: var(--radius) !important;
            transition: border-color 0.2s !important;
        }
        [data-testid="stFileUploader"]:hover {
            border-color: var(--accent) !important;
        }

        /* ── Buttons ── */
        .stButton > button {
            background: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 0.92rem !important;
            padding: 0.6rem 1.8rem !important;
            letter-spacing: 0.02em !important;
            transition: opacity 0.2s, transform 0.1s !important;
            box-shadow: 0 4px 15px rgba(59,130,246,0.25) !important;
        }
        .stButton > button:hover {
            opacity: 0.9 !important;
            transform: translateY(-1px) !important;
        }
        .stButton > button:active { transform: translateY(0) !important; }

        /* Download button — subdued variant */
        .stDownloadButton > button {
            background: var(--bg-hover) !important;
            color: var(--text) !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            font-size: 0.88rem !important;
            transition: border-color 0.2s !important;
        }
        .stDownloadButton > button:hover {
            border-color: var(--accent) !important;
            color: #93c5fd !important;
        }

        /* ── Inputs ── */
        .stTextInput input, .stSelectbox select {
            background: var(--bg-card) !important;
            color: var(--text) !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px !important;
        }
        .stTextInput input:focus {
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 2px rgba(59,130,246,0.2) !important;
        }

        /* ── Alerts / banners ── */
        .stAlert {
            border-radius: var(--radius) !important;
            border: 1px solid var(--border) !important;
            background: var(--bg-card) !important;
        }

        /* ── Expander ── */
        .streamlit-expanderHeader {
            background: var(--bg-card) !important;
            border-radius: var(--radius) !important;
            color: var(--text) !important;
            font-weight: 600 !important;
        }

        /* ── Report markdown output ── */
        .report-container {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 2rem 2.5rem;
            font-size: 0.9rem;
            line-height: 1.7;
        }
        .report-container h1 { color: #e2e8f0; font-size: 1.5rem; }
        .report-container h2 { color: #cbd5e1; font-size: 1.15rem; border-bottom: 1px solid var(--border); padding-bottom: 0.4rem; margin-top: 1.8rem; }
        .report-container h3 { color: #94a3b8; font-size: 0.95rem; }
        .report-container table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
        .report-container th { background: #1a2235; color: var(--text-dim); padding: 0.5rem 0.8rem; text-align: left; border: 1px solid var(--border); }
        .report-container td { padding: 0.45rem 0.8rem; border: 1px solid var(--border); color: var(--text); }
        .report-container tr:nth-child(even) td { background: rgba(255,255,255,0.02); }
        .report-container blockquote { border-left: 3px solid var(--accent); padding-left: 1rem; color: var(--text-dim); margin: 1rem 0; }
        .report-container code { background: rgba(59,130,246,0.12); color: #93c5fd; padding: 2px 6px; border-radius: 4px; font-size: 0.82rem; }

        /* ── Scrollbar ── */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: var(--bg-deep); }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--accent); }

        /* ── Hide Streamlit branding ── */
        #MainMenu, footer, header { visibility: hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Helper: run an async coroutine from synchronous Streamlit context
# ---------------------------------------------------------------------------

def _run_async(coro):
    """
    Run an async coroutine from a synchronous context (Streamlit's main thread).
    Uses a fresh event loop to avoid conflicts with any existing loop.
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# Helper: build InvestigationState from a parsed DataFrame
# ---------------------------------------------------------------------------

def _build_initial_state(case_name: str, df: pd.DataFrame):
    """
    Convert the raw uploaded DataFrame into an InvestigationState with
    CommentData objects in state.raw_comments.

    The SecurityAgent will re-validate and sanitise these rows during its
    pipeline stage; we only need a best-effort parse here to populate the
    initial state container.

    Args:
        case_name: User-supplied case name string.
        df:        DataFrame loaded from the uploaded CSV.

    Returns:
        A populated InvestigationState instance.
    """
    # Import backend models (deferred to avoid startup overhead)
    from src.core.state import CommentData, InvestigationState

    raw_comments = []
    for idx, row in df.iterrows():
        try:
            # Parse timestamp — be lenient so various date formats are accepted
            raw_ts = row.get("Timestamp", row.get("timestamp", ""))
            try:
                ts = pd.to_datetime(raw_ts).to_pydatetime()
            except Exception:
                ts = datetime.now(timezone.utc)

            comment_data = CommentData(
                comment_id=str(uuid.uuid4()),
                platform=str(row.get("Platform", row.get("platform", "Unknown"))),
                username=str(row.get("Username", row.get("username", "unknown"))),
                timestamp=ts,
                comment_text=str(row.get("Comment", row.get("comment", ""))),
            )
            raw_comments.append(comment_data)
        except Exception:
            # Skip malformed rows silently; the SecurityAgent will handle validation
            continue

    return InvestigationState(
        case_id=f"CASE-{uuid.uuid4().hex[:8].upper()}",
        case_name=case_name.strip(),
        raw_comments=raw_comments,
    )


# ---------------------------------------------------------------------------
# Helper: derive summary metrics from the completed state
# ---------------------------------------------------------------------------

_HARMFUL_CATEGORIES = frozenset({"Harassment", "Hate Speech", "Threat", "Possible Defamation"})


def _derive_metrics(state) -> dict:
    """
    Compute the four key display metrics from the final InvestigationState.

    Returns a dict with keys:
        total, harmful, campaign_detected, campaign_confidence,
        category_counter, platform_counter
    """
    total = len(state.sanitized_comments)
    harmful = 0
    category_counter: Counter = Counter()
    platform_counter: Counter = Counter()

    for comment in state.sanitized_comments:
        platform_counter[comment.platform] += 1
        for cat in comment.categories:
            category_counter[cat] += 1
            if cat in _HARMFUL_CATEGORIES:
                harmful += 1
                break  # count each comment at most once as harmful

    # Campaign is detected when at least one cluster has ≥ 2 members
    non_trivial_clusters = {
        cid: members
        for cid, members in state.campaign_clusters.items()
        if len(members) >= 2
    }
    campaign_detected = len(non_trivial_clusters) > 0

    # Approximate confidence: ratio of cluster members to total comments
    total_cluster_members = sum(len(m) for m in non_trivial_clusters.values())
    campaign_confidence = (
        min(total_cluster_members / total, 0.97) if total > 0 else 0.0
    )

    return {
        "total": total,
        "harmful": harmful,
        "campaign_detected": campaign_detected,
        "campaign_confidence": campaign_confidence,
        "category_counter": category_counter,
        "platform_counter": platform_counter,
    }


# ---------------------------------------------------------------------------
# UI Components
# ---------------------------------------------------------------------------

def _render_hero() -> None:
    """Render the top hero banner with logo, title, and tagline."""
    st.markdown(
        """
        <div class="apex-hero">
            <div class="apex-badge">⚖️ &nbsp; Decision Support &nbsp;·&nbsp; AI-Powered</div>
            <h1>Apex Legal AI</h1>
            <p>AI-powered evidence intelligence for online harassment investigations</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_metric_tiles(metrics: dict) -> None:
    """
    Render the four summary metric tiles in a responsive CSS grid.

    Args:
        metrics: Dict produced by _derive_metrics().
    """
    campaign_label = "DETECTED" if metrics["campaign_detected"] else "CLEAR"
    campaign_color = "value-red" if metrics["campaign_detected"] else "value-green"
    campaign_accent = "accent-red" if metrics["campaign_detected"] else "accent-green"
    confidence_pct = f"{metrics['campaign_confidence'] * 100:.1f}%"

    harmful_pct = (
        f"{metrics['harmful'] / metrics['total'] * 100:.1f}% of total"
        if metrics["total"] > 0 else "—"
    )

    st.markdown(
        f"""
        <div class="metric-grid">
            <div class="metric-tile">
                <div class="mt-accent-bar accent-blue"></div>
                <div class="mt-label">Total Comments</div>
                <div class="mt-value value-blue">{metrics['total']}</div>
                <div class="mt-sub">After sanitisation</div>
            </div>
            <div class="metric-tile">
                <div class="mt-accent-bar accent-red"></div>
                <div class="mt-label">Harmful Comments</div>
                <div class="mt-value value-red">{metrics['harmful']}</div>
                <div class="mt-sub">{harmful_pct}</div>
            </div>
            <div class="metric-tile">
                <div class="mt-accent-bar {campaign_accent}"></div>
                <div class="mt-label">Campaign Status</div>
                <div class="mt-value {campaign_color}">{campaign_label}</div>
                <div class="mt-sub">Coordinated activity signal</div>
            </div>
            <div class="metric-tile">
                <div class="mt-accent-bar accent-amber"></div>
                <div class="mt-label">Cluster Confidence</div>
                <div class="mt-value value-amber">{confidence_pct}</div>
                <div class="mt-sub">Message clustering score</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_stage_tracker(stage_records: list, current_idx: int = -1) -> None:
    """
    Render a horizontal pill-row showing each pipeline stage status.

    Args:
        stage_records: List of StageRecord objects from PipelineResult.
        current_idx:   Index of the stage currently running (-1 = all done).
    """
    # Import StageStatus only when needed
    from src.core.orchestrator import StageStatus

    pills_html = '<div class="stage-tracker">'
    for i, record in enumerate(stage_records):
        if record.status == StageStatus.COMPLETED:
            cls, icon = "done", "✓"
        elif record.status == StageStatus.FAILED:
            cls, icon = "failed", "✗"
        elif i == current_idx:
            cls, icon = "running", "◉"
        else:
            cls, icon = "", "○"

        elapsed = f" · {record.elapsed_ms:.0f} ms" if record.elapsed_ms > 0 else ""
        pills_html += (
            f'<div class="stage-pill {cls}">'
            f'<span>{icon}</span>{record.agent_name}{elapsed}'
            f"</div>"
        )
    pills_html += "</div>"
    st.markdown(pills_html, unsafe_allow_html=True)


def _render_category_breakdown(category_counter: Counter, total: int) -> None:
    """
    Render a category breakdown bar-chart section using Streamlit's native
    bar_chart component.  Falls back to a simple table for empty datasets.

    Args:
        category_counter: Frequency count of each analysis category.
        total:            Total sanitised comment count.
    """
    if not category_counter:
        st.info("No category data available.")
        return

    # Build a tidy DataFrame for the chart
    chart_df = pd.DataFrame(
        [
            {"Category": cat, "Comments": count}
            for cat, count in sorted(category_counter.items(), key=lambda x: -x[1])
        ]
    ).set_index("Category")

    st.bar_chart(chart_df, use_container_width=True, color="#3b82f6")


def _render_platform_breakdown(platform_counter: Counter) -> None:
    """
    Render a platform distribution table.

    Args:
        platform_counter: Frequency count of each platform string.
    """
    if not platform_counter:
        st.info("No platform data available.")
        return

    rows = [
        {"Platform": p, "Comments": n, "Share": f"{n / sum(platform_counter.values()) * 100:.1f}%"}
        for p, n in platform_counter.most_common()
    ]
    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
    )


def _render_evidence_table(state) -> None:
    """
    Render a filterable evidence table of sanitised comments, sorted by severity.

    Args:
        state: The final InvestigationState.
    """
    if not state.sanitized_comments:
        st.info("No sanitised comments available.")
        return

    rows = []
    for comment in state.sanitized_comments:
        try:
            sev_int = int(comment.severity or 0)
        except (ValueError, TypeError):
            sev_int = 0

        rows.append({
            "Platform":  comment.platform,
            "Username":  comment.username,
            "Timestamp": comment.timestamp.strftime("%Y-%m-%d %H:%M") if comment.timestamp else "—",
            "Category":  ", ".join(comment.categories) if comment.categories else (comment.severity or "—"),
            "Severity":  sev_int,
            "Comment":   comment.comment_text[:200] + ("…" if len(comment.comment_text) > 200 else ""),
        })

    df = pd.DataFrame(rows).sort_values("Severity", ascending=False)

    # Severity filter slider
    max_sev = int(df["Severity"].max()) if not df.empty else 5
    min_filter = st.slider(
        "Filter — minimum severity",
        min_value=0,
        max_value=5,
        value=0,
        step=1,
        help="Show only comments at or above this severity level.",
    )
    filtered = df[df["Severity"] >= min_filter]

    st.caption(f"Showing {len(filtered)} of {len(df)} comments")
    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Severity": st.column_config.NumberColumn(
                "Severity",
                min_value=0,
                max_value=5,
                format="%d / 5",
            ),
            "Comment": st.column_config.TextColumn("Comment", width="large"),
        },
    )


def _render_campaign_clusters(state) -> None:
    """
    Render a summary of detected campaign clusters.

    Args:
        state: The final InvestigationState.
    """
    non_trivial = {
        cid: members
        for cid, members in state.campaign_clusters.items()
        if len(members) >= 2
    }

    if not non_trivial:
        st.success("No coordinated campaign clusters were detected above threshold.")
        return

    st.warning(
        f"⚠️  {len(non_trivial)} campaign cluster(s) detected "
        f"exhibiting characteristics consistent with coordinated activity.",
        icon=None,
    )

    cluster_rows = [
        {"Cluster ID": cid, "Members": len(members), "Comment Indices": ", ".join(members[:8]) + ("…" if len(members) > 8 else "")}
        for cid, members in sorted(non_trivial.items())
    ]
    st.dataframe(
        pd.DataFrame(cluster_rows),
        use_container_width=True,
        hide_index=True,
    )


def _render_report(state) -> None:
    """
    Render the Markdown investigation report inside a styled container with
    a Download Report button.

    Args:
        state: The final InvestigationState (must have report_draft_markdown set).
    """
    report_md = state.report_draft_markdown or ""

    if not report_md:
        st.warning("No report was generated. Check pipeline logs for errors.")
        return

    # ── Download button (above report for discoverability) ──────────────────
    col_dl, col_info = st.columns([2, 5])
    with col_dl:
        st.download_button(
            label="⬇  Download Report (.md)",
            data=report_md.encode("utf-8"),
            file_name=f"{state.case_id}_investigation_report.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col_info:
        st.caption(
            f"Report for **{state.case_name}** · Case ID: `{state.case_id}` · "
            f"{len(report_md):,} characters"
        )

    st.markdown("<hr class='apex-divider'>", unsafe_allow_html=True)

    # ── Render the Markdown inside a styled scroll container ─────────────────
    st.markdown(
        f'<div class="report-container">{_md_to_html_safe(report_md)}</div>',
        unsafe_allow_html=True,
    )


def _md_to_html_safe(md_text: str) -> str:
    """
    Convert Markdown to HTML using the `markdown` stdlib module when available,
    falling back to wrapping the raw Markdown in a `<pre>` block.  The HTML
    is embedded inside the `report-container` div which styles it correctly.
    """
    try:
        import markdown as md_lib  # optional dependency
        return md_lib.markdown(
            md_text,
            extensions=["tables", "fenced_code", "nl2br"],
        )
    except ImportError:
        # Fallback: render as a plain preformatted block; Streamlit's own
        # st.markdown() is used as an escape hatch in the caller.
        pass

    # Second fallback: use Streamlit's native markdown renderer inside expander
    # (we return a sentinel so the caller knows to use st.markdown instead)
    return f"<pre style='white-space:pre-wrap;color:#e2e8f0'>{md_text}</pre>"


# ---------------------------------------------------------------------------
# Sidebar content
# ---------------------------------------------------------------------------

def _render_sidebar() -> None:
    """Render sidebar navigation info and compliance notice."""
    with st.sidebar:
        st.markdown(
            """
            <div style="padding:1rem 0 0.5rem">
                <div style="font-size:1.3rem;font-weight:800;color:#e2e8f0;">⚖️ Apex Legal AI</div>
                <div style="font-size:0.72rem;color:#6b7280;text-transform:uppercase;
                            letter-spacing:0.1em;margin-top:4px;">Evidence Intelligence</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<hr class='apex-divider'>", unsafe_allow_html=True)

        st.markdown("**Pipeline Agents**")
        agents = [
            ("🔒", "Security Agent",  "PII scrubbing & validation"),
            ("📂", "Evidence Agent",  "Structured data extraction"),
            ("🧠", "Analysis Agent",  "Toxicity classification"),
            ("🕵️", "Campaign Agent",  "Cluster & burst detection"),
            ("📄", "Report Agent",    "Markdown report generation"),
        ]
        for icon, name, desc in agents:
            st.markdown(
                f"<div style='padding:0.3rem 0;font-size:0.82rem;'>"
                f"<span style='color:#6b7280'>{icon}</span> "
                f"<span style='color:#e2e8f0;font-weight:500'>{name}</span><br>"
                f"<span style='color:#4b5563;font-size:0.74rem;padding-left:1.2rem'>{desc}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<hr class='apex-divider'>", unsafe_allow_html=True)

        # CSV format hint
        with st.expander("📋 CSV Format Guide", expanded=False):
            st.markdown(
                """
                Your CSV must contain these columns:

                | Column | Description |
                |---|---|
                | `Username` | Account identifier |
                | `Comment` | Raw comment text |
                | `Timestamp` | ISO 8601 datetime |
                | `Platform` | Source platform |

                Additional columns are preserved but not required.
                """
            )

        st.markdown("<hr class='apex-divider'>", unsafe_allow_html=True)

        st.markdown(
            "<div style='font-size:0.72rem;color:#4b5563;line-height:1.5'>"
            "⚖️ <strong style='color:#6b7280'>Legal Notice:</strong> "
            "Apex Legal AI provides decision support only. "
            "No output constitutes legal advice."
            "</div>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Main investigation runner
# ---------------------------------------------------------------------------

def _run_investigation(case_name: str, uploaded_file) -> None:
    """
    Core investigation workflow triggered when the user clicks Run Investigation.

    Steps:
    1. Parse the uploaded CSV into a DataFrame.
    2. Build the initial InvestigationState.
    3. Instantiate the ApexLegalOrchestrator.
    4. Run the async pipeline via _run_async().
    5. Display progress, metrics, tabs, and the final report.

    Args:
        case_name:     User-supplied case name.
        uploaded_file: Streamlit UploadedFile object.
    """
    # ── Step 1: Parse CSV ────────────────────────────────────────────────────
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as exc:
        st.error(f"❌ Failed to parse CSV file: {exc}")
        return

    # Validate that the minimum required columns exist before hitting the backend
    required_cols = {"Username", "Comment", "Timestamp", "Platform"}
    missing = required_cols - set(df.columns)
    if missing:
        st.error(
            f"❌ CSV is missing required columns: **{', '.join(sorted(missing))}**\n\n"
            "See the CSV Format Guide in the sidebar for the expected schema."
        )
        return

    if df.empty:
        st.warning("The uploaded file contains no rows.")
        return

    st.success(f"✅ CSV loaded — {len(df):,} rows detected.")

    # ── Step 2: Build initial state ──────────────────────────────────────────
    with st.spinner("Building investigation state…"):
        try:
            initial_state = _build_initial_state(case_name, df)
        except Exception as exc:
            st.error(f"❌ Failed to build InvestigationState: {exc}")
            return

    # ── Step 3 & 4: Run the pipeline ─────────────────────────────────────────
    st.markdown("<hr class='apex-divider'>", unsafe_allow_html=True)
    st.markdown("**🔄 Running Investigation Pipeline**")

    # Import backend (deferred)
    try:
        from src.core.orchestrator import ApexLegalOrchestrator
    except Exception as exc:
        st.error(f"❌ Failed to import orchestrator: {exc}")
        return

    pipeline_placeholder = st.empty()
    error_placeholder = st.empty()

    try:
        with st.spinner("Executing multi-agent pipeline… This may take a moment."):
            orchestrator = ApexLegalOrchestrator(config_path="config/adk_config.yaml")
            result = _run_async(orchestrator.execute_investigation(initial_state))
    except Exception as exc:
        st.error(f"❌ Pipeline execution failed: {exc}")
        return

    # ── Display stage tracker ────────────────────────────────────────────────
    with pipeline_placeholder.container():
        _render_stage_tracker(result.stages)

    # Surface any pipeline-level errors
    if not result.pipeline_ok:
        failed = result.failed_stages
        error_placeholder.error(
            f"⚠️ Pipeline completed with {len(failed)} error(s): "
            + "; ".join(s.error_message or "unknown" for s in failed)
        )
    else:
        error_placeholder.success(
            f"✅ Pipeline completed in {result.total_elapsed_ms / 1000:.2f}s"
        )

    # Store result in session state so it persists across Streamlit reruns
    st.session_state["pipeline_result"] = result
    st.session_state["initial_df"] = df


def _render_results() -> None:
    """
    Render all results sections from the stored PipelineResult.
    Called after a successful or partial pipeline execution.
    """
    result = st.session_state.get("pipeline_result")
    if result is None:
        return

    state = result.state
    metrics = _derive_metrics(state)

    st.markdown("<hr class='apex-divider'>", unsafe_allow_html=True)
    st.markdown("### 📊 Investigation Summary")

    # Four headline metric tiles
    _render_metric_tiles(metrics)

    # Tabbed detail sections
    tab_analysis, tab_evidence, tab_campaign, tab_report = st.tabs([
        "📈 Analysis",
        "📋 Evidence Table",
        "🕵️ Campaign Clusters",
        "📄 Full Report",
    ])

    with tab_analysis:
        st.markdown("#### Category Distribution")
        _render_category_breakdown(metrics["category_counter"], metrics["total"])
        st.markdown("#### Platform Breakdown")
        _render_platform_breakdown(metrics["platform_counter"])

    with tab_evidence:
        st.markdown("#### Sanitised Evidence")
        _render_evidence_table(state)

    with tab_campaign:
        st.markdown("#### Coordinated Campaign Clusters")
        _render_campaign_clusters(state)

    with tab_report:
        st.markdown("#### Investigation Report")
        _render_report(state)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Main Streamlit application entry point.

    Layout:
    - Sidebar: agent reference panel and CSV format guide
    - Hero banner: title and tagline
    - Upload form: case name + CSV uploader + run button
    - Results: metrics, analysis tabs, report (rendered after a pipeline run)
    """
    _inject_css()
    _render_sidebar()
    _render_hero()

    # ── Upload / case configuration form ────────────────────────────────────
    with st.container():
        st.markdown("### 🗂  New Investigation")

        col_name, col_upload = st.columns([2, 3], gap="large")

        with col_name:
            case_name = st.text_input(
                "Case Name",
                placeholder="e.g. Project Nightfall — Q3 2026",
                help="A descriptive name for this investigation case.",
                key="case_name_input",
            )
            st.markdown(
                "<div style='font-size:0.78rem;color:#4b5563;margin-top:-0.4rem'>"
                "Used to identify the case in the generated report."
                "</div>",
                unsafe_allow_html=True,
            )

        with col_upload:
            uploaded_file = st.file_uploader(
                "Upload Case Dataset (CSV)",
                type=["csv"],
                help="CSV must contain: Username, Comment, Timestamp, Platform",
                key="csv_uploader",
            )

        # ── Preview uploaded file ───────────────────────────────────────────
        if uploaded_file is not None:
            try:
                preview_df = pd.read_csv(io.BytesIO(uploaded_file.read()))
                uploaded_file.seek(0)  # reset for later read
                with st.expander(
                    f"📄 Preview: {uploaded_file.name} · {len(preview_df):,} rows",
                    expanded=False,
                ):
                    st.dataframe(preview_df.head(10), use_container_width=True)
            except Exception:
                pass  # preview failure is non-fatal

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Run Investigation button ────────────────────────────────────────
        run_disabled = not (case_name.strip() and uploaded_file is not None)
        run_clicked = st.button(
            "⚡  Run Investigation",
            disabled=run_disabled,
            use_container_width=False,
            key="run_button",
        )

        if run_disabled and not run_clicked:
            st.caption("Enter a case name and upload a CSV file to enable the investigation.")

    # ── Trigger pipeline on button press ────────────────────────────────────
    if run_clicked and case_name.strip() and uploaded_file is not None:
        # Clear any previous run's results before starting fresh
        st.session_state.pop("pipeline_result", None)
        _run_investigation(case_name=case_name.strip(), uploaded_file=uploaded_file)

    # ── Render results (persists across reruns via session_state) ───────────
    _render_results()


# ---------------------------------------------------------------------------
# Streamlit entry
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
else:
    # When Streamlit imports the module, call main() directly
    main()
