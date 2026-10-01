# Report Agent implementation. Generates structured case file markdown from evidence data.
#
# Receives the fully-populated InvestigationState after the Campaign Agent has run
# and assembles a professional Markdown investigation report.  The report is stored
# in state.report_draft_markdown and is never written to disk by this agent —
# file export is delegated to the MCP layer per workspace policy.

import logging
import re
import textwrap
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from src.core.state import CommentData, InvestigationState

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Categories that are counted as harmful/flagged in report totals.
_HARMFUL_CATEGORIES: frozenset = frozenset(
    {"Harassment", "Hate Speech", "Threat", "Possible Defamation", "Spam"}
)

# Severity labels corresponding to severity_score integers 1–5 stored in
# CommentData.severity.  Used to render a human-readable severity scale.
_SEVERITY_LABELS: Dict[str, str] = {
    "1": "Negligible",
    "2": "Low",
    "3": "Moderate",
    "4": "High",
    "5": "Critical",
}

# Category-to-confidence mapping: defines normalized confidence scores for
# each category when the API does not provide explicit confidence.
# These values reflect our confidence in classification accuracy per category.
_CATEGORY_CONFIDENCE_MAP: Dict[str, float] = {
    "Threat": 0.95,                    # Highest confidence for explicit threats
    "Hate Speech": 0.92,               # Strong confidence for hate speech detection
    "Harassment": 0.90,                # Strong confidence for harassment patterns
    "Possible Defamation": 0.90,       # Strong confidence for defamation signals
    "Spam": 0.85,                      # Moderate-high for spam detection (often repetitive)
    "Safe": 0.99,                      # Very high confidence for Safe classification
}

# Maximum number of individual evidence rows to render verbatim in the
# Evidence Summary section.  Keeps the report readable when datasets are large.
_MAX_EVIDENCE_ROWS = 50

# Width (in characters) used when wrapping long comment excerpts.
_EXCERPT_WRAP_WIDTH = 100

# Entity extraction regex patterns for different entity types
_ENTITY_PATTERNS = {
    "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    "url": re.compile(r'https?://[^\s]+|www\.[^\s]+'),
    "phone": re.compile(r'\+?1?\s*\(?[0-9]{3}\)?[\s.-]?[0-9]{3}[\s.-]?[0-9]{4}'),
    "hashtag": re.compile(r'#[A-Za-z0-9_]+'),
    "mention": re.compile(r'@[A-Za-z0-9_]+'),
}


def _classified_records(state: InvestigationState) -> List[Any]:
    """Return EvidenceRecord-like objects when the Evidence Agent populated them."""
    return list(getattr(state, "evidence_records", []) or [])


def _record_severity(record: Any) -> Optional[str]:
    severity = getattr(record, "severity", None)
    if severity is None:
        return None
    return str(severity)


def _extract_entities_from_text(text: str) -> Dict[str, Set[str]]:
    """
    Extract various entity types from a text comment.

    Returns a dict mapping entity type names to sets of extracted values.
    """
    entities: Dict[str, Set[str]] = {
        "email": set(),
        "url": set(),
        "phone": set(),
        "hashtag": set(),
        "mention": set(),
    }

    for entity_type, pattern in _ENTITY_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            entities[entity_type].update(matches)

    return entities


def _confidence_display(confidence: Any, category: Optional[str] = None) -> str:
    """
    Display confidence score with category-based normalization.

    If confidence is provided, uses it; otherwise, falls back to category-based
    mappings from _CATEGORY_CONFIDENCE_MAP for consistency.

    Args:
        confidence: Explicit confidence value (0-1 or already a percentage string).
        category:   Category name to use for fallback mapping (e.g. 'Threat', 'Spam').

    Returns:
        Formatted confidence string (e.g., '95%', '-' for None).
    """
    # If explicit confidence provided, normalize and display it
    if confidence is not None:
        try:
            conf_value = float(confidence)
            # Assume 0-1 range if < 1, else assume it's already a percentage
            if conf_value <= 1.0:
                conf_value *= 100
            return f"{conf_value:.0f}%"
        except (TypeError, ValueError):
            pass

    # Fallback to category-based mapping for consistency
    if category and category in _CATEGORY_CONFIDENCE_MAP:
        mapped_conf = _CATEGORY_CONFIDENCE_MAP[category]
        return f"{mapped_conf * 100:.0f}%"

    return "-"

# ---------------------------------------------------------------------------
# Formatting helpers (pure functions — no side effects)
# ---------------------------------------------------------------------------

def _now_utc_iso() -> str:
    """Return the current UTC time formatted as an ISO 8601 string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _fmt_dt(dt: Optional[datetime]) -> str:
    """
    Format a datetime object as a readable string.
    Handles timezone-aware and timezone-naive objects uniformly.
    Returns 'N/A' for None values.
    """
    if dt is None:
        return "N/A"
    try:
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return str(dt)


def _escape_md(text: str) -> str:
    """
    Escape a handful of Markdown special characters that would break table
    cells or inline code in the rendered report.  Only targets characters that
    are genuinely problematic inside table cells or inline contexts.
    """
    # Pipe characters break GFM table columns; newlines break rows.
    return text.replace("|", "\\|").replace("\n", " ").replace("\r", "")


def _truncate(text: str, max_chars: int = 120) -> str:
    """
    Truncate text to *max_chars* characters, appending an ellipsis when
    truncation occurs.  Used to keep evidence table cells compact.
    """
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "…"


def _severity_badge(severity_raw: Optional[str]) -> str:
    """
    Convert a raw severity string (e.g. '3') to a human-readable badge string.
    Falls back gracefully when the value is missing or non-numeric.
    """
    if not severity_raw:
        return "—"
    label = _SEVERITY_LABELS.get(severity_raw.strip(), None)
    if label:
        return f"{severity_raw} / {label}"
    return severity_raw


def _category_emoji(category: str) -> str:
    """
    Return a small emoji indicator for each analysis category to improve
    visual scannability of the Markdown table.
    """
    mapping = {
        "Safe": "✅",
        "Spam": "📧",
        "Harassment": "⚠️",
        "Hate Speech": "🚨",
        "Threat": "🔴",
        "Possible Defamation": "⚖️",
    }
    return mapping.get(category, "❓")


# ---------------------------------------------------------------------------
# Section builders — each returns a Markdown string for one report section
# ---------------------------------------------------------------------------

def _build_header(state: InvestigationState, generated_at: str) -> str:
    """
    Build the report title block, case metadata table, and generation timestamp.
    """
    case_created = _fmt_dt(state.created_at)

    return textwrap.dedent(f"""\
        # 🔍 Apex Legal AI — Investigation Report

        > **DECISION SUPPORT DOCUMENT — NOT LEGAL ADVICE**
        > This report is generated by an automated AI system. It characterises
        > observable statistical and linguistic patterns only. It does not
        > constitute legal advice, a determination of legal guilt, or a
        > recommendation to take any specific legal or law-enforcement action.

        ---

        ## Case Overview

        | Field | Value |
        |---|---|
        | **Case ID** | `{_escape_md(state.case_id)}` |
        | **Case Name** | {_escape_md(state.case_name)} |
        | **Investigation Created** | {case_created} |
        | **Report Generated** | {generated_at} |
        | **Pipeline Status** | Complete |

    """)


def _build_statistics(
    state: InvestigationState,
    harmful_count: int,
    category_counter: Counter,
    severity_counter: Counter,
) -> str:
    """
    Build the quantitative statistics section: total comments, harmful counts,
    category breakdown, and severity distribution.

    Args:
        state:            The completed investigation state.
        harmful_count:    Number of comments classified in a harmful category.
        category_counter: Frequency count of each analysis category.
        severity_counter: Frequency count of each severity score string.
    """
    total = len(state.sanitized_comments)
    raw_total = len(state.raw_comments)

    # Determine the percentage of harmful comments, guarding against /0
    harmful_pct = (harmful_count / total * 100) if total > 0 else 0.0

    # Build the category breakdown rows
    category_rows = "\n".join(
        f"| {_category_emoji(cat)} {cat} | {count} | "
        f"{count / total * 100:.1f}% |"
        for cat, count in sorted(category_counter.items(), key=lambda x: -x[1])
    ) if total > 0 else "| — | — | — |"

    # Build severity distribution rows
    severity_rows = "\n".join(
        f"| {_severity_badge(sev)} | {count} |"
        for sev, count in sorted(severity_counter.items())
    ) if severity_counter else "| — | — |"

    return textwrap.dedent(f"""\
        ---

        ## 📊 Statistical Summary

        | Metric | Value |
        |---|---|
        | **Total Raw Comments Received** | {raw_total} |
        | **Comments After Sanitisation** | {total} |
        | **Harmful Comments Detected** | {harmful_count} ({harmful_pct:.1f}%) |
        | **Safe / Benign Comments** | {total - harmful_count} |
        | **Unique Comment Clusters** | {len(state.campaign_clusters)} |
        | **Distinct Entity Types Extracted** | {len(state.extracted_entities)} |

        ### Category Breakdown

        | Category | Count | % of Total |
        |---|---|---|
        {category_rows}

        ### Severity Distribution

        | Severity | Count |
        |---|---|
        {severity_rows}

    """)


def _build_campaign_section(state: InvestigationState) -> str:
    """
    Build the campaign detection section with enriched cluster details.

    The CampaignAgent stores its cluster map in state.campaign_clusters as
    Dict[str, List[str]] (cluster_id → [comment_index_strings]).  This section
    renders enriched cluster details: repeated message text, affected accounts,
    platforms, time range, and confidence.

    A campaign is considered detected when at least one non-trivial cluster
    (≥ 2 members) is present in the state.
    """
    clusters = state.campaign_clusters
    comments = state.sanitized_comments

    # Determine campaign status from the cluster map stored by CampaignAgent
    non_trivial = {
        cid: members
        for cid, members in clusters.items()
        if len(members) >= 2
    }
    campaign_detected = len(non_trivial) > 0

    if campaign_detected:
        detection_badge = "🔴 **DETECTED**"
        detection_intro = (
            f"{len(non_trivial)} cluster(s) of repeated or near-identical messages "
            "from multiple accounts were identified, exhibiting characteristics "
            "consistent with coordinated activity."
        )
    else:
        detection_badge = "🟢 **NOT DETECTED**"
        detection_intro = (
            "No similarity clusters meeting the minimum threshold were identified "
            "in the submitted dataset."
        )

    # Build enriched cluster detail rows when clusters exist
    cluster_details_rows: List[str] = []

    if non_trivial:
        records = _classified_records(state)
        # Build a mapping from comment index to record for enrichment
        comment_index_map = {idx: record for idx, record in enumerate(records)} if records else {}

        for cluster_id, member_indices in sorted(non_trivial.items()):
            member_count = len(member_indices)

            # Extract sample comment text from the first member
            sample_comment_idx = int(member_indices[0])
            if sample_comment_idx < len(comments):
               sample_text = _truncate(
    comments[sample_comment_idx].comment_text or "",
    80,
)
            else:
                sample_text = "(comment text unavailable)"

            # Extract affected usernames and platforms
            affected_users = set()
            affected_platforms = set()
            timestamps: List[datetime] = []

            for idx_str in member_indices:
                idx = int(idx_str)
                if idx < len(comments):
                    c = comments[idx]
                    if c.username:
                        affected_users.add(c.username)
                    if c.platform:
                        affected_platforms.add(c.platform)
                    if c.timestamp:
                        timestamps.append(c.timestamp)

            users_str = ", ".join(sorted(affected_users)[:3])
            if len(affected_users) > 3:
                users_str += f" (+{len(affected_users) - 3} more)"
            platforms_str = ", ".join(sorted(affected_platforms)) or "Unknown"

            # Determine time range
            if timestamps:
                time_min = min(timestamps)
                time_max = max(timestamps)
                time_range = f"{_fmt_dt(time_min)} to {_fmt_dt(time_max)}"
            else:
                time_range = "N/A"

            # Get confidence from first record in cluster if available
            confidence_str = "-"
            if sample_comment_idx in comment_index_map:
                record = comment_index_map[sample_comment_idx]
                category = getattr(record, "category", None)
                confidence = getattr(record, "confidence", None)
                confidence_str = _confidence_display(confidence, category)

            cluster_details_rows.append(
                f"| {cluster_id} | {member_count} | "
                f"{_escape_md(sample_text)} | {_escape_md(users_str)} | "
                f"{_escape_md(platforms_str)} | {time_range} | {confidence_str} |"
            )

    cluster_section = ""
    if cluster_details_rows:
        cluster_header = textwrap.dedent("""\
            ### Campaign Cluster Details

            | Cluster | Members | Repeated Message | Affected Accounts | Platforms | Time Range | Confidence |
            |---|---|---|---|---|---|---|
        """)
        cluster_section = cluster_header + "\n".join(cluster_details_rows) + "\n"

    return textwrap.dedent(f"""\
        ---

        ## 🕵️ Campaign Detection

        **Status:** {detection_badge}

        {detection_intro}

        {cluster_section}""")


def _build_evidence_summary(state: InvestigationState) -> str:
    """
    Build the evidence summary section with enriched columns.

    Renders a paginated GFM table of sanitised comments (capped at
    _MAX_EVIDENCE_ROWS to keep the report readable).  Comments are sorted
    by detected severity (highest first) so reviewers see the most
    concerning items at the top.

    Each row includes: index, platform, username, timestamp, category,
    severity, confidence, comment excerpt (60 chars), and explanation.
    """
    records = _classified_records(state)
    comments = state.sanitized_comments

    if records:
        def _sort_record(record: Any) -> Tuple:
            try:
                sev = int(getattr(record, "severity", None) or 0)
            except (ValueError, TypeError):
                sev = 0
            return (-sev, getattr(record, "category", "") or "")

        sorted_records = sorted(records, key=_sort_record)
        display_records = sorted_records[:_MAX_EVIDENCE_ROWS]
        truncation_notice = ""
        if len(sorted_records) > _MAX_EVIDENCE_ROWS:
            truncation_notice = (
                f"\n> **Table truncated.** Showing {_MAX_EVIDENCE_ROWS} of "
                f"{len(sorted_records)} comments (sorted by severity, highest first).\n\n"
            )

        rows: List[str] = []
        for idx, record in enumerate(display_records, start=1):
            primary_cat = getattr(record, "category", None) or "-"
            cat_display = f"{_category_emoji(primary_cat)} {primary_cat}"
            confidence = getattr(record, "confidence", None)
            explanation = getattr(record, "explanation", None) or "-"
            comment_text = getattr(record, "comment", "") or ""

            rows.append(
                f"| {idx} "
                f"| {_escape_md(getattr(record, 'platform', '') or '')} "
                f"| {_escape_md(getattr(record, 'username', '') or '')} "
                f"| {_fmt_dt(getattr(record, 'timestamp', None))} "
                f"| {_escape_md(cat_display)} "
                f"| {_severity_badge(_record_severity(record))} "
                f"| {_confidence_display(confidence, primary_cat)} "
                f"| {_escape_md(_truncate(comment_text, 60))} "
                f"| {_escape_md(_truncate(explanation, 80))} |"
            )

        return (
            "---\n\n"
            "## 📋 Evidence Summary\n"
            f"{truncation_notice}"
            "| # | Platform | Username | Timestamp | Category | Severity | Confidence | Comment | Explanation |\n"
            "|---|---|---|---|---|---|---|---|---|\n"
            f"{chr(10).join(rows)}\n"
        )

    if not comments:
        return textwrap.dedent("""\
            ---

            ## 📋 Evidence Summary

            No sanitised comments were available for this report.

        """)

    # Fallback: display from CommentData when no records
    return textwrap.dedent("""\
        ---

        ## 📋 Evidence Summary

        No analysed evidence records available (pipeline may not have completed).

    """)


def _build_analysis_summary(
    state: InvestigationState,
    harmful_count: int,
) -> str:
    """
    Build the AI analysis summary section — narrative interpretation
    of the statistical findings.
    """
    total = len(state.sanitized_comments)
    records = _classified_records(state)

    # Determine the most common harmful category
    harmful_categories = Counter()
    for record in records:
        cat = getattr(record, "category", None)
        if cat and cat in _HARMFUL_CATEGORIES:
            harmful_categories[cat] += 1

    dominant_harmful = harmful_categories.most_common(1)[0][0] if harmful_categories else "N/A"
    dominant_harmful_str = f"**{dominant_harmful}**" if dominant_harmful != "N/A" else "N/A"
    top_harmful_str = (
        ", ".join(f"{cat} ({n})" for cat, n in harmful_categories.most_common(3))
        if harmful_categories
        else "None"
    )

    # Platform frequency
    platform_counter = Counter(
        c.platform for c in state.sanitized_comments if c.platform
    )
    top_platforms = platform_counter.most_common(3)
    platform_str = (
        ", ".join(f"{p} ({n})" for p, n in top_platforms)
        if top_platforms else "N/A"
    )

    # Entity type summary
    entity_summary = (
        ", ".join(sorted(state.extracted_entities.keys()))
        if state.extracted_entities
        else "No entity types extracted."
    )

    # Campaign signal phrasing
    has_clusters = any(
        len(m) >= 2 for m in state.campaign_clusters.values()
    )
    campaign_sentence = (
        "Campaign analysis identified clustered message patterns exhibiting "
        "characteristics consistent with coordinated multi-account activity."
        if has_clusters
        else
        "Campaign analysis did not identify coordinated activity patterns "
        "that met the detection thresholds."
    )

    return textwrap.dedent(f"""\
        ---

        ## 🤖 AI Analysis Summary

        The automated analysis pipeline processed **{total}** sanitised comments
        for case **{_escape_md(state.case_name)}**.

        Of the total dataset, **{harmful_count}** comment(s) were classified into
        one or more harmful categories.

        **Dominant harmful category:** {dominant_harmful_str}.

        Harm category signals observed: {top_harmful_str}.

        Activity was distributed across the following platforms: {platform_str}.

        {campaign_sentence}

        **Extracted Entity Types:** {entity_summary}

        > **Note:** All classifications above are produced by an AI model and
        > represent statistical assessments of linguistic content only.  They do
        > not determine factual accuracy, legal validity, or individual culpability.

    """)


def _build_human_review_section(
    state: InvestigationState,
    harmful_count: int,
) -> str:
    """
    Build the Human Review Required section.

    Lists the specific review actions that a qualified human reviewer should
    perform before any action is taken based on this report.  The checklist
    is calibrated to the severity of findings in the dataset.
    """
    total = len(state.sanitized_comments)
    records = _classified_records(state)
    if records:
        has_critical = any(_record_severity(record) == "5" for record in records)
    else:
        has_critical = any(
            c.severity == "5" for c in state.sanitized_comments
        )
    has_campaign = any(
        len(m) >= 2 for m in state.campaign_clusters.values()
    )

    # Build context-sensitive checklist items
    checklist_items = [
        "- [ ] Verify the completeness and integrity of the source dataset.",
        "- [ ] Review all comments classified as **Threat** or **Hate Speech** "
               "individually before taking any action.",
        "- [ ] Confirm that AI-assigned categories accurately reflect the context "
               "of each comment (false positives are possible).",
        "- [ ] Cross-reference extracted entity identifiers against case records "
               "to confirm relevance.",
    ]

    if has_critical:
        checklist_items.insert(
            1,
            "- [ ] ⚠️ **PRIORITY:** One or more comments received a severity score "
               "of **5 (Critical)**. These should be reviewed immediately by a "
               "qualified case manager.",
        )

    if has_campaign:
        checklist_items.append(
            "- [ ] Evaluate the identified message clusters for coordinated behaviour "
               "patterns. Verify that affected accounts are not false positives "
               "(e.g., legitimate shared templates or quoted content)."
        )

    if harmful_count == 0:
        checklist_items.append(
            "- [ ] Confirm that the absence of harmful content is consistent with "
               "manual review of a sample of comments."
        )

    checklist_str = "\n".join(checklist_items)

    return textwrap.dedent(f"""\
        ---

        ## 👁️ Human Review Required

        This AI-generated report **must be reviewed by a qualified human** before
        any action is taken. The following checklist items require attention:

        {checklist_str}

        | Review Item | Status |
        |---|---|
        | AI classification spot-checked | ☐ Pending |
        | Source dataset verified | ☐ Pending |
        | Campaign clusters confirmed | ☐ Pending |
        | Case manager sign-off | ☐ Pending |

    """)


def _build_disclaimer() -> str:
    """
    Build the legal disclaimer section.

    This section is mandatory and must appear at the end of every report
    generated by Apex Legal AI per workspace compliance policy.
    """
    return textwrap.dedent("""\
        ---

        ## ⚖️ Legal Disclaimer

        **Apex Legal AI does not provide legal advice.**

        This report and all content within it is produced by an automated
        artificial intelligence system for informational and decision-support
        purposes only. It is not a substitute for advice from a licensed legal
        professional.

        Specifically:

        - This report does **not** constitute legal advice of any kind.
        - This report does **not** determine or imply legal guilt, liability,
          or criminal culpability of any individual or organisation.
        - This report does **not** recommend any specific legal, civil, or
          law-enforcement action.
        - AI classification results are statistical in nature and may contain
          errors, omissions, or false positives/negatives.
        - Any decision to take action based on this report must be made by a
          qualified human professional who has independently verified the
          findings presented herein.

        All content in this report is governed by the Apex Legal AI Terms of
        Service and applicable data protection legislation.

        ---
        *Report generated by Apex Legal AI Automated Pipeline*
        *Classification: CONFIDENTIAL — For Authorised Recipients Only*
    """)


# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------

def _assemble_report(state: InvestigationState, generated_at: str) -> str:
    """
    Coordinate all section builders into a single coherent Markdown document.

    Args:
        state: The fully-populated InvestigationState from the pipeline.
        generated_at: Timestamp string for report generation time.

    Returns:
        A single Markdown string ready for export or display.
    """
    records = _classified_records(state)
    comments = state.sanitized_comments

    # Compute statistics for the section builders
    harmful_count = 0
    category_counter: Counter = Counter()
    severity_counter: Counter = Counter()

    if records:
        for record in records:
            cat = getattr(record, "category", None)
            sev = _record_severity(record)
            if cat in _HARMFUL_CATEGORIES:
                harmful_count += 1
            if cat:
                category_counter[cat] += 1
            if sev:
                severity_counter[sev] += 1

    # Assemble all sections
    sections = [
        _build_header(state, generated_at),
        _build_statistics(state, harmful_count, category_counter, severity_counter),
        _build_campaign_section(state),
        _build_evidence_summary(state),
        _build_analysis_summary(state, harmful_count),
        _build_human_review_section(state, harmful_count),
        _build_disclaimer(),
    ]

    return "\n".join(sections)


# ---------------------------------------------------------------------------
# ReportAgent class
# ---------------------------------------------------------------------------

class ReportAgent:
    """
    Generates structured investigation reports from completed InvestigationState.

    The ReportAgent is the final stage of the five-agent pipeline. It receives
    a fully-populated InvestigationState (after Campaign Agent has run) and
    assembles a professional Markdown report summarising all findings.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def run(self, state: InvestigationState) -> InvestigationState:
        """
        Generate the investigation report and populate state.report_draft_markdown.

        Args:
            state: Completed investigation state with all agent outputs populated.

        Returns:
            Updated state with report_draft_markdown populated.
        """
        try:
            generated_at = _now_utc_iso()
            report_markdown = _assemble_report(state, generated_at)
            state.report_draft_markdown = report_markdown
            self.logger.info(
                f"Report generated successfully for case {state.case_id}. "
                f"Report size: {len(report_markdown)} characters."
            )
        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}", exc_info=True)
            state.report_draft_markdown = (
                f"# ❌ Report Generation Failed\n\n"
                f"An error occurred while generating the investigation report:\n\n"
                f"```\n{str(e)}\n```\n\n"
                f"Please review the pipeline logs for detailed error information."
            )

        return state
