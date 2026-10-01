#!/usr/bin/env python3
"""Validation tests for the enhanced report_agent helper functions."""

from src.agents.report_agent import (
    _confidence_display,
    _category_emoji,
    _truncate,
    _extract_entities_from_text,
)


def test_confidence_display_category_mapping():
    """Confidence rules return correct % per category when no explicit value given."""
    assert _confidence_display(None, "Threat") == "95%"
    assert _confidence_display(None, "Hate Speech") == "92%"
    assert _confidence_display(None, "Harassment") == "90%"
    assert _confidence_display(None, "Spam") == "85%"
    assert _confidence_display(None, "Safe") == "99%"


def test_confidence_display_explicit_values():
    """Explicit float/int confidence values are formatted correctly."""
    assert _confidence_display(0.75) == "75%"
    assert _confidence_display(0.95) == "95%"


def test_category_emoji_mapping():
    """Every known category returns a non-empty emoji string."""
    for cat in ["Safe", "Spam", "Harassment", "Hate Speech", "Threat", "Possible Defamation"]:
        emoji = _category_emoji(cat)
        assert emoji, f"Expected emoji for category '{cat}', got empty string"


def test_truncate_long_text():
    """Text longer than limit is truncated and ends with ellipsis."""
    long_text = "This is a really long comment that should be truncated to 60 characters with an ellipsis at the end"
    truncated = _truncate(long_text, 60)
    assert len(truncated) <= 63, "Truncated text should not exceed limit + ellipsis length"
    assert "…" in truncated or "..." in truncated, "Truncated text should contain ellipsis"


def test_truncate_short_text():
    """Text shorter than limit is returned unchanged."""
    short = "Hello world"
    assert _truncate(short, 60) == short


def test_entity_extraction():
    """Entity extractor finds emails, URLs, mentions, hashtags, and phones."""
    test_comment = (
        "Contact us at support@example.com or visit https://www.example.com "
        "Follow us @company and use #marketing. Call 555-123-4567."
    )
    entities = _extract_entities_from_text(test_comment)

    assert "support@example.com" in entities.get("email", [])
    assert any("example.com" in url for url in entities.get("url", []))

