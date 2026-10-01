#!/usr/bin/env python
"""Tests for campaign detection and report generation pipeline."""

import asyncio
from datetime import datetime, timedelta

from src.agents.campaign_agent import CampaignAgent, CampaignConfig
from src.agents.report_agent import ReportAgent
from src.core.state import InvestigationState, CommentData


def _make_state() -> InvestigationState:
    base_ts = datetime(2024, 1, 15, 10, 0, 0)
    return InvestigationState(
        case_id="TEST-001",
        case_name="Test Campaign Detection",
        sanitized_comments=[
            CommentData(comment_id="1", platform="twitter", username="user1",
                        timestamp=base_ts, comment_text="Ban this lawyer!", severity="High"),
            CommentData(comment_id="2", platform="twitter", username="user2",
                        timestamp=base_ts + timedelta(minutes=1), comment_text="Ban this lawyer!", severity="High"),
            CommentData(comment_id="3", platform="twitter", username="user3",
                        timestamp=base_ts + timedelta(minutes=2), comment_text="Ban this lawyer!", severity="High"),
            CommentData(comment_id="4", platform="twitter", username="user4",
                        timestamp=base_ts + timedelta(hours=1), comment_text="I disagree with the law", severity="Low"),
        ],
    )


def test_campaign_agent_populates_clusters():
    """Campaign agent detects repeated harmful message across 3 users."""
    state = _make_state()
    config = CampaignConfig(similarity_threshold=0.65, min_cluster_size=2, burst_threshold=3)
    updated = asyncio.run(CampaignAgent(config=config).run(state))
    assert len(updated.campaign_clusters) >= 1, "Should detect at least one campaign cluster"


def test_report_agent_produces_markdown():
    """ReportAgent produces non-empty markdown after campaign detection."""
    state = _make_state()
    config = CampaignConfig(similarity_threshold=0.65, min_cluster_size=2, burst_threshold=3)
    state = asyncio.run(CampaignAgent(config=config).run(state))
    state = asyncio.run(ReportAgent().run(state))

    assert state.report_draft_markdown is not None
    assert len(state.report_draft_markdown) > 100
