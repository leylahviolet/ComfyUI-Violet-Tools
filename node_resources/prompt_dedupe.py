# -*- coding: utf-8 -*-
"""Shared utilities for prompt deduplication across all Violet Tools nodes."""


def dedupe_and_clean_prompt(text: str) -> str:
    """
    Deduplicate comma-separated phrases and clean up malformed commas.
    
    Preserves order of first occurrence. Deduplicates whole phrases between commas,
    not individual words. Also fixes double commas and excessive spacing around commas.
    
    Args:
        text (str): Raw prompt text with potential duplicates and comma issues
        
    Returns:
        str: Cleaned prompt with duplicates removed and commas normalized
        
    Examples:
        >>> dedupe_and_clean_prompt("purple hair, purple hair, blue eyes")
        'purple hair, blue eyes'
        >>> dedupe_and_clean_prompt("mystical landscape, mystical landscape, mystical landscape")
        'mystical landscape'
        >>> dedupe_and_clean_prompt("text,, more text, , even more")
        'text, more text, even more'
    """
    if not text or not isinstance(text, str):
        return text if isinstance(text, str) else ""
    
    # Step 1: Split by commas and strip whitespace from each phrase
    phrases = [phrase.strip() for phrase in text.split(",")]
    
    # Step 2: Deduplicate while preserving order (case-sensitive to match SD prompt behavior)
    seen = set()
    unique_phrases = []
    for phrase in phrases:
        if phrase and phrase not in seen:
            seen.add(phrase)
            unique_phrases.append(phrase)
    
    # Step 3: Rejoin with proper comma-space formatting
    result = ", ".join(unique_phrases)
    
    return result
