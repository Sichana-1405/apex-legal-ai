#!/usr/bin/env python3
"""
Comprehensive tests for the enhanced ReportAgent.
Verifies confidence rules, report structure, and section content.
"""

import asyncio
from datetime import datetime, timezone

from src.core.state import InvestigationState, CommentData
from src.agents.report_agent import ReportAgent, _confidence_display


def _make_state() -> InvestigationState:
    """Minimal investigation state with representative test data."""
    comments = [
        CommentData(
            comment_id="c1", platform="Twitter", username="user1",
            timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            comment_text="Kill yourself you stupid idiot",
            categories=["Threat"], severity="5",
        ),
        CommentData(
            comment_id="c2", platform="Instagram", username="user2",
            timestamp=datetime(2024, 1, 15, 10, 5, 0, tzinfo=timezone.utc),
            comment_text="Kill yourself you stupid idiot",
            categories=["Threat"], severity="5",
        ),
        CommentData(
            comment_id="c3", platform="Facebook", username="user3",
            timestamp=datetime(2024, 1, 15, 10, 10, 0, tzinfo=timezone.utc),
            comment_text="This is spam, buy now at https://scam.com!",
            categories=["Spam"], severity="2",
        ),
        CommentData(
            comment_id="c4", platform="Twitter", username="user4",
            timestamp=datetime(2024, 1, 15, 10, 15, 0, tzinfo=timezone.utc),
            comment_text="Great product, would recommend",
            categories=["Safe"], severity="1",
        ),
    ]
    return InvestigationState(
        case_id="CASE-2024-001",
        case_name="Test Campaign Detection Case",
        created_at=datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc),
        sanitized_comments=comments,
        campaign_clusters={"cluster_0": ["0", "1"]},
        extracted_entities={"email": ["support@example.com"], "url": ["https://scam.com"]},
    )


def test_confidence_scoring_rules():
    """Confidence rules return correct percentages per category."""
    assert _confidence_display(None, "Threat") == "95%"
    assert _confidence_display(None, "Safe") == "99%"
    assert _confidence_display(None, "Harassment") == "90%"
    assert _confidence_display(None, "Spam") == "85%"
    assert _confidence_display(None, "Hate Speech") == "92%"


def test_full_report_generation():
    """ReportAgent.run() produces a non-empty markdown report."""
    state = _make_state()
    updated = asyncio.run(ReportAgent().run(state))
    report = updated.report_draft_markdown
    assert report is not None, "Report should not be None"
    assert len(report) > 100, "Report should contain meaningful content"


def test_report_contains_key_sections():
    """Report markdown includes all expected top-level sections."""
    state = _make_state()
    updated = asyncio.run(ReportAgent().run(state))
    report = updated.report_draft_markdown
    for section in ["Case Overview", "Statistical Summary", "Evidence Summary"]:
        assert section in report, f"Report should contain '{section}' section"


def test_report_reflects_classifications():
    """Report content reflects Threat and Safe categories from state."""
    state = _make_state()
    updated = asyncio.run(ReportAgent().run(state))
    report = updated.report_draft_markdown
    assert "Threat" in report
    assert "Safe" in report
