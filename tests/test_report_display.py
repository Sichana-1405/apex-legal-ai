#!/usr/bin/env python
"""Quick test to verify campaign detection works and report can be generated."""

import asyncio
from datetime import datetime, timedelta
from src.agents.campaign_agent import CampaignAgent, CampaignConfig
from src.agents.report_agent import ReportAgent
from src.agents.evidence_agent import EvidenceRecord
from src.core.state import InvestigationState, CommentData

async def test_full_pipeline():
    """Test the full campaign detection and report generation."""
    
    # Create test state with repeated harmful messages
    base_ts = datetime(2024, 1, 15, 10, 0, 0)
    
    state = InvestigationState(
        case_id="TEST-001",
        case_name="Test Campaign Detection",
    )
    
    # Add sanitized comments (flagged ones, not Safe)
    state.sanitized_comments = [
        CommentData(
            comment_id="1",
            platform="twitter",
            username="user1",
            timestamp=base_ts,
            comment_text="Ban this lawyer!",
            severity="High",
        ),
        CommentData(
            comment_id="2",
            platform="twitter",
            username="user2",
            timestamp=base_ts + timedelta(minutes=1),
            comment_text="Ban this lawyer!",
            severity="High",
        ),
        CommentData(
            comment_id="3",
            platform="twitter",
            username="user3",
            timestamp=base_ts + timedelta(minutes=2),
            comment_text="Ban this lawyer!",
            severity="High",
        ),
        CommentData(
            comment_id="4",
            platform="twitter",
            username="user4",
            timestamp=base_ts + timedelta(hours=1),
            comment_text="I disagree with the law",
            severity="Low",
        ),
    ]
    
    # Run campaign agent
    config = CampaignConfig(similarity_threshold=0.65, min_cluster_size=2, burst_threshold=3)
    campaign_agent = CampaignAgent(config=config)
    state = await campaign_agent.run(state)
    
    print("=" * 60)
    print("CAMPAIGN DETECTION RESULTS")
    print("=" * 60)
    print(f"Campaign Clusters: {state.campaign_clusters}")
    print(f"Cluster count: {len(state.campaign_clusters)}")
    print(f"State campaign_clusters populated: {bool(state.campaign_clusters)}")
    print()
    
    # Run report agent
    report_agent = ReportAgent()
    state = await report_agent.run(state)
    
    print("=" * 60)
    print("REPORT GENERATION RESULTS")
    print("=" * 60)
    print(f"Report generated: {bool(state.report_draft_markdown)}")
    if state.report_draft_markdown:
        report_lines = state.report_draft_markdown.split('\n')
        print(f"Report length: {len(state.report_draft_markdown)} chars, {len(report_lines)} lines")
        print("\nFirst 500 chars of report:")
        print("-" * 60)
        print(state.report_draft_markdown[:500])
        print("-" * 60)
        print("\n✓ Full pipeline working! Report is ready for display.")
    else:
        print("✗ Report generation failed!")
    
    return state

if __name__ == "__main__":
    state = asyncio.run(test_full_pipeline())
