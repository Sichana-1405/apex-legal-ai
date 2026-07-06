"""
Test suite for Campaign Detection Agent.

Tests clustering, cross-user coordination detection, and temporal burst analysis
using realistic harassment campaign datasets with repeated harmful messages.
"""

import pytest
from datetime import datetime, timedelta
from typing import List

from src.agents.campaign_agent import (
    CampaignAgent,
    CampaignConfig,
    CampaignResult,
)
from src.agents.evidence_agent import EvidenceRecord


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def base_timestamp() -> datetime:
    """A consistent base timestamp for testing."""
    return datetime(2024, 1, 15, 10, 0, 0)


@pytest.fixture
def campaign_config_lenient() -> CampaignConfig:
    """Campaign config with lowered thresholds for testing."""
    return CampaignConfig(
        similarity_threshold=0.65,
        min_cluster_size=2,
        min_unique_accounts=2,
        burst_window_minutes=60,
        burst_threshold=3,
        high_confidence_cutoff=0.97,
    )


def create_evidence_record(
    row_number: int,
    username: str,
    comment: str,
    timestamp: datetime,
    platform: str = "twitter",
) -> EvidenceRecord:
    """Helper to create an EvidenceRecord."""
    return EvidenceRecord(
        row_number=row_number,
        username=username,
        comment=comment,
        timestamp=timestamp,
        platform=platform,
    )


# ---------------------------------------------------------------------------
# Test: Repeated Harassment Comments (Multi-Account Coordination)
# ---------------------------------------------------------------------------

def test_campaign_detection_repeated_harassment_multiuser(
    base_timestamp: datetime,
    campaign_config_lenient: CampaignConfig,
) -> None:
    """
    Test campaign detection when identical harassment messages are posted by
    multiple distinct accounts in coordinated bursts.

    This simulates a realistic scenario where:
    - The same defamatory or harassing message is repeated across accounts
    - Multiple accounts post the repeated message within a short time window
    - Temporal clustering indicates coordination
    """
    agent = CampaignAgent(config=campaign_config_lenient)

    # Simulate a coordinated harassment campaign: the same defamatory message
    # repeated by different accounts in rapid succession (within 5 minutes)
    records: List[EvidenceRecord] = [
        create_evidence_record(
            0, "user_alice", "This CEO is a fraud and should be in jail!", base_timestamp
        ),
        create_evidence_record(
            1, "user_bob", "This CEO is a fraud and should be in jail!", base_timestamp + timedelta(minutes=1)
        ),
        create_evidence_record(
            2, "user_charlie", "This CEO is a fraud and should be in jail!", base_timestamp + timedelta(minutes=2)
        ),
        create_evidence_record(
            3, "user_diane", "This CEO is a fraud and should be in jail!", base_timestamp + timedelta(minutes=3)
        ),
        # Add one different message to show that the cluster is specific to the repeated message
        create_evidence_record(
            4, "user_eve", "I disagree with the company's policy on layoffs", base_timestamp + timedelta(minutes=30)
        ),
    ]

    result: CampaignResult = agent.detect(records)

    # Assertions
    assert result.campaign_detected is True, "Should detect a coordinated campaign"
    assert result.confidence_score > 0.6, "Confidence should be significant"
    assert len(result.affected_accounts) >= 4, "Should identify all 4 coordinating accounts"
    assert result.repeated_message is not None, "Should identify the repeated message"
    assert result.burst_count >= 3, "Should detect a temporal burst of 3+ messages"
    assert result.total_comments_analyzed == 5, "Should analyze all 5 comments"
    print(f"✓ Multi-user coordination detected: {result.confidence_score:.2%} confidence")
    print(f"  Affected accounts: {result.affected_accounts}")
    print(f"  Repeated message: {result.repeated_message[:60]}...")
    print(f"  Burst count: {result.burst_count}")


# ---------------------------------------------------------------------------
# Test: Near-Identical Messages (Variation Detection)
# ---------------------------------------------------------------------------

def test_campaign_detection_near_identical_messages(
    base_timestamp: datetime,
    campaign_config_lenient: CampaignConfig,
) -> None:
    """
    Test that the agent clusters near-identical messages that vary slightly
    (e.g., with typos, punctuation changes, or minor wording variations).

    This tests the TF-IDF similarity matching against realistic variations.
    """
    agent = CampaignAgent(config=campaign_config_lenient)

    # Simulate near-identical harassment messages with minor variations
    records: List[EvidenceRecord] = [
        create_evidence_record(0, "troll_1", "Death to all lawyers!", base_timestamp),
        create_evidence_record(1, "troll_2", "Death to all lawyers!!", base_timestamp + timedelta(minutes=2)),
        create_evidence_record(2, "troll_3", "death to all lawyers", base_timestamp + timedelta(minutes=4)),
        create_evidence_record(3, "troll_4", "Death 2 all lawyers", base_timestamp + timedelta(minutes=6)),
        create_evidence_record(4, "neutral_user", "I have questions about lawyer ethics", base_timestamp + timedelta(hours=1)),
    ]

    result: CampaignResult = agent.detect(records)

    # Assertions
    assert result.campaign_detected is True, "Should detect coordinated use of near-identical threats"
    assert len(result.affected_accounts) >= 4, "Should identify all 4 troll accounts"
    assert result.confidence_score > 0.5, "Should have reasonable confidence despite variations"
    print(f"✓ Near-identical threat variants detected: {result.confidence_score:.2%} confidence")
    print(f"  Cluster size: {result.burst_count}")


# ---------------------------------------------------------------------------
# Test: Mixed Safe and Harmful Comments (Filtering)
# ---------------------------------------------------------------------------

def test_campaign_agent_with_safe_comments(
    base_timestamp: datetime,
    campaign_config_lenient: CampaignConfig,
) -> None:
    """
    Test that the agent correctly handles a mix of harmful and neutral comments.
    (This test operates at the detect() level, not the state-based run() level.)
    """
    agent = CampaignAgent(config=campaign_config_lenient)

    # Mix harmful coordinated messages with neutral comments
    records: List[EvidenceRecord] = [
        # Neutral/Safe comments
        create_evidence_record(0, "user_a", "Great article about company strategy", base_timestamp),
        create_evidence_record(1, "user_b", "I like the new product launch", base_timestamp + timedelta(minutes=10)),
        # Coordinated harmful campaign
        create_evidence_record(2, "attacker_1", "This company exploits workers", base_timestamp + timedelta(minutes=20)),
        create_evidence_record(3, "attacker_2", "This company exploits workers", base_timestamp + timedelta(minutes=21)),
        create_evidence_record(4, "attacker_3", "This company exploits workers", base_timestamp + timedelta(minutes=22)),
        # More neutral comments
        create_evidence_record(5, "user_c", "Looking forward to earnings report", base_timestamp + timedelta(minutes=30)),
    ]

    result: CampaignResult = agent.detect(records)

    # The coordinated harmful messages should still be detected
    assert result.campaign_detected is True, "Should detect campaign despite mixed content"
    assert result.total_comments_analyzed == 6, "Should analyze all 6 comments"
    print(f"✓ Campaign detected in mixed safe/harmful dataset: {result.confidence_score:.2%} confidence")


# ---------------------------------------------------------------------------
# Test: Empty Dataset
# ---------------------------------------------------------------------------

def test_campaign_detection_empty_dataset(
    campaign_config_lenient: CampaignConfig,
) -> None:
    """Test graceful handling of empty input."""
    agent = CampaignAgent(config=campaign_config_lenient)
    result: CampaignResult = agent.detect([])

    assert result.campaign_detected is False
    assert result.confidence_score == 0.0
    assert result.total_comments_analyzed == 0
    print("✓ Empty dataset handled gracefully")


# ---------------------------------------------------------------------------
# Test: No Coordinated Activity (Single User Spam)
# ---------------------------------------------------------------------------

def test_campaign_detection_single_user_spam(
    base_timestamp: datetime,
    campaign_config_lenient: CampaignConfig,
) -> None:
    """
    Test that a single user posting the same message many times is NOT
    flagged as a coordinated campaign (requires cross-user signal).
    """
    agent = CampaignAgent(config=campaign_config_lenient)

    # Same user posting identical spam repeatedly
    records: List[EvidenceRecord] = [
        create_evidence_record(
            i,
            "spammer_bob",  # Same user
            "Click here for free money!",
            base_timestamp + timedelta(minutes=i),
        )
        for i in range(5)
    ]

    result: CampaignResult = agent.detect(records)

    # Should NOT be flagged as a coordinated campaign
    # (single user does not satisfy min_unique_accounts requirement)
    cross_user_signal = len(result.affected_accounts) >= campaign_config_lenient.min_unique_accounts
    assert not cross_user_signal, "Single user spam should not trigger cross-user signal"
    print(f"✓ Single-user spam correctly NOT flagged as coordinated: {result.confidence_score:.2%}")
    print(f"  Unique accounts: {len(result.affected_accounts)}")


# ---------------------------------------------------------------------------
# Test: Temporal Burst Detection
# ---------------------------------------------------------------------------

def test_campaign_detection_temporal_burst(
    base_timestamp: datetime,
    campaign_config_lenient: CampaignConfig,
) -> None:
    """
    Test that temporal bursts (rapid clustering of messages) are correctly detected
    and contribute to confidence scoring.
    """
    agent = CampaignAgent(config=campaign_config_lenient)

    # Coordinated burst: identical messages from multiple users within 10 minutes
    records: List[EvidenceRecord] = [
        create_evidence_record(0, "user_1", "Ban this lawyer!", base_timestamp),
        create_evidence_record(1, "user_2", "Ban this lawyer!", base_timestamp + timedelta(minutes=1)),
        create_evidence_record(2, "user_3", "Ban this lawyer!", base_timestamp + timedelta(minutes=3)),
        create_evidence_record(3, "user_4", "Ban this lawyer!", base_timestamp + timedelta(minutes=5)),
        # Message posted much later (outside burst window)
        create_evidence_record(4, "user_5", "Ban this lawyer!", base_timestamp + timedelta(hours=2)),
    ]

    result: CampaignResult = agent.detect(records)

    assert result.campaign_detected is True
    assert result.burst_count >= 3, "Should detect burst of 3+ messages within 60-min window"
    print(f"✓ Temporal burst detected: {result.burst_count} messages within window")
    print(f"  Confidence: {result.confidence_score:.2%}")


# ---------------------------------------------------------------------------
# Test: Cluster Size Requirement
# ---------------------------------------------------------------------------

def test_campaign_detection_below_min_cluster_size(
    base_timestamp: datetime,
    campaign_config_lenient: CampaignConfig,
) -> None:
    """
    Test that a cluster below min_cluster_size does not trigger campaign detection.
    """
    agent = CampaignAgent(config=campaign_config_lenient)

    # Only 1 matching message — below min_cluster_size of 2
    records: List[EvidenceRecord] = [
        create_evidence_record(0, "user_1", "Kill this journalist", base_timestamp),
        create_evidence_record(1, "user_2", "I support press freedom", base_timestamp + timedelta(minutes=10)),
        create_evidence_record(2, "user_3", "Journalism is important", base_timestamp + timedelta(minutes=20)),
    ]

    result: CampaignResult = agent.detect(records)

    assert result.campaign_detected is False, "Single message should not trigger detection"
    assert result.total_comments_analyzed == 3
    print("✓ Below-threshold cluster correctly not flagged as campaign")


if __name__ == "__main__":
    # Run all tests with pytest
    pytest.main([__file__, "-v", "-s"])
