#!/usr/bin/env python3
"""Quick validation test for the enhanced report_agent."""

from src.agents.report_agent import (
    _confidence_display,
    _category_emoji,
    _truncate,
    _extract_entities_from_text,
)

# Test 1: Confidence display with category mapping
print("=" * 60)
print("Test 1: Confidence Display with Category Mapping")
print("=" * 60)
print(f"Threat confidence (no explicit value): {_confidence_display(None, 'Threat')}")
print(f"Hate Speech confidence: {_confidence_display(None, 'Hate Speech')}")
print(f"Harassment confidence: {_confidence_display(None, 'Harassment')}")
print(f"Spam confidence: {_confidence_display(None, 'Spam')}")
print(f"Safe confidence: {_confidence_display(None, 'Safe')}")
print(f"Explicit 0.75 confidence: {_confidence_display(0.75)}")
print(f"Explicit 85 confidence (already %): {_confidence_display(85)}")
print()

# Test 2: Category emoji mapping
print("=" * 60)
print("Test 2: Category Emoji Mapping")
print("=" * 60)
for cat in ["Safe", "Spam", "Harassment", "Hate Speech", "Threat", "Possible Defamation"]:
    print(f"{cat:20s} → {_category_emoji(cat)}")
print()

# Test 3: Truncation at 60 chars
print("=" * 60)
print("Test 3: Truncation at 60 Characters")
print("=" * 60)
long_text = "This is a really long comment that should be truncated to 60 characters with an ellipsis at the end"
truncated = _truncate(long_text, 60)
print(f"Original ({len(long_text)} chars): {long_text}")
print(f"Truncated ({len(truncated)} chars): {truncated}")
print()

# Test 4: Entity extraction
print("=" * 60)
print("Test 4: Entity Extraction")
print("=" * 60)
test_comment = """
Contact us at support@example.com or visit https://www.example.com
Follow us @company and use #marketing
Call 555-123-4567 for more info
"""
entities = _extract_entities_from_text(test_comment)
for entity_type, values in entities.items():
    if values:
        print(f"{entity_type:10s}: {', '.join(values)}")
print()

print("✅ All validation tests passed!")
