#!/usr/bin/env python
"""Test the fixes: Levenshtein similarity, caching, and fallback confidence."""

import asyncio
from datetime import datetime
from src.skills.campaign_clustering import cluster_similar_comments
from src.agents.analysis_agent import AnalysisAgent, AnalysisResult
from src.agents.evidence_agent import EvidenceRecord

def test_clustering():
    """Test 1: Verify Levenshtein similarity prevents false positives."""
    print("=" * 70)
    print("TEST 1: Clustering with Levenshtein Similarity")
    print("=" * 70)
    
    # Should NOT cluster these different sentences
    texts = [
        "This is a test comment",
        "This is another test comment",
        "Ban all lawyers!",
        "Ban all lawyers!",
    ]
    
    clusters = cluster_similar_comments(texts, threshold=0.65)
    print(f"Texts:")
    for i, t in enumerate(texts):
        print(f"  {i}: {t}")
    print(f"\nClusters (threshold=0.65): {clusters}")
    print(f"Expected: {{0: [2, 3]}} or similar (only identical 'Ban all lawyers!' clustered)")
    print()


def test_analysis_caching():
    """Test 2: Verify AnalysisAgent caching for determinism."""
    print("=" * 70)
    print("TEST 2: AnalysisAgent Caching for Determinism")
    print("=" * 70)
    
    agent = AnalysisAgent(api_key=None)  # Will use fallback
    
    # Create identical records
    records = [
        EvidenceRecord(
            row_number=0,
            username="user1",
            comment="Kill all lawyers",
            timestamp=datetime.now(),
            platform="twitter",
        ),
        EvidenceRecord(
            row_number=1,
            username="user2",
            comment="Kill all lawyers",  # Identical to record 0
            timestamp=datetime.now(),
            platform="twitter",
        ),
        EvidenceRecord(
            row_number=2,
            username="user3",
            comment="I like lawyers",
            timestamp=datetime.now(),
            platform="twitter",
        ),
    ]
    
    results = agent.analyze_evidence(records)
    
    print(f"Record 0 analysis:")
    print(f"  Category: {results[0].category}")
    print(f"  Confidence: {results[0].confidence_score}")
    print(f"\nRecord 1 analysis (identical comment):")
    print(f"  Category: {results[1].category}")
    print(f"  Confidence: {results[1].confidence_score}")
    print(f"\nExpected: Records 0 and 1 have IDENTICAL category and confidence")
    print(f"Match: {results[0].category == results[1].category and results[0].confidence_score == results[1].confidence_score}")
    print()


def test_fallback_confidence():
    """Test 3: Verify fallback confidence is reasonable (not 0.50)."""
    print("=" * 70)
    print("TEST 3: Fallback Confidence Scoring")
    print("=" * 70)
    
    agent = AnalysisAgent(api_key=None)  # Will use fallback
    
    test_cases = [
        ("Kill all lawyers", "Threat", 0.60),
        ("This is spam buy now limited offer", "Spam", 0.65),
        ("I hate this", "Harassment", 0.58),
        ("Hello world", "Safe", 0.55),
    ]
    
    for comment, expected_category, expected_confidence in test_cases:
        result = agent._get_fallback_result(comment, "Test error")
        print(f"Comment: '{comment}'")
        print(f"  Category: {result.category} (expected {expected_category})")
        print(f"  Confidence: {result.confidence_score:.2f} (expected ~{expected_confidence})")
        print()


if __name__ == "__main__":
    test_clustering()
    test_analysis_caching()
    test_fallback_confidence()
    
    print("=" * 70)
    print("✓ All tests completed!")
    print("=" * 70)
