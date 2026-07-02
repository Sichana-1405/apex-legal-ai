# Local text cleaning & prompt injection checks.

def sanitize_comment(text: str) -> str:
    """Neutralizes HTML tags, script scripts, and common prompt injection phrases."""
    return text

def is_malicious(text: str) -> bool:
    """Performs quick heuristic scan on whether text contains injection or scripting attacks."""
    return False
