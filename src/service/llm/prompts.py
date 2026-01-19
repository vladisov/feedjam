"""Prompt templates for LLM operations."""

SYSTEM_CONTENT_PROCESSOR = """You are a content analysis assistant. You analyze articles and provide structured information about them. Always respond with valid JSON."""

PROCESS_ITEMS_PROMPT = """Analyze these articles and return a JSON response.

Articles:
{items}

For each article, provide:
- title: A cleaned, concise title (max 80 characters). If the original title is already short and clear, return null. Otherwise, shorten and improve readability while preserving the key meaning.
- summary: A concise 1-2 sentence summary (MAX 250 characters). Focus on the key insight or news. Be direct, no filler phrases like "This article discusses...".
- topics: 3-5 keyword topics for categorization (lowercase, single words or hyphenated phrases)
- quality: A score from 0.0 to 1.0 based on:
  - Informativeness: Does it provide real value/information?
  - Clarity: Is it well-written and easy to understand?
  - Substance: Is it substantive content vs clickbait/fluff?

Return JSON in this exact format:
{{
  "results": [
    {{"title": "..." or null, "summary": "...", "topics": ["topic1", "topic2"], "quality": 0.8}},
    ...
  ]
}}

Analyze {count} articles. Return exactly {count} results in the same order."""


def format_items_for_processing(items: list) -> str:
    """Format items for the processing prompt."""
    formatted = []
    for i, item in enumerate(items, 1):
        text = f"[{i}] Title: {item.title}"
        if item.content:
            # Truncate content to avoid token limits
            content = item.content[:1500] + "..." if len(item.content) > 1500 else item.content
            text += f"\nContent: {content}"
        formatted.append(text)
    return "\n\n".join(formatted)


SYSTEM_RELEVANCE_SCORER = """You are a content relevance scorer. You evaluate how relevant articles are to a user's interests. Always respond with valid JSON."""

SCORE_RELEVANCE_PROMPT = """Score the relevance of these articles to the user's profile.

User Interests: {interests}
User's Preferred Sources: {liked_sources}

Articles:
{items}

For each article, provide a relevance score from 0.0 to 1.0:
- 0.0-0.3: Not relevant to user's interests
- 0.4-0.6: Somewhat relevant
- 0.7-0.9: Highly relevant
- 1.0: Perfectly matches user's interests

Return JSON:
{{
  "scores": [0.8, 0.3, 0.7, ...]
}}

Score {count} articles. Return exactly {count} scores in the same order."""


def format_items_for_relevance(items: list) -> str:
    """Format items for relevance scoring prompt."""
    formatted = []
    for i, item in enumerate(items, 1):
        text = f"[{i}] {item.title}"
        if hasattr(item, "source_name") and item.source_name:
            text += f" (from {item.source_name})"
        if hasattr(item, "summary") and item.summary:
            text += f"\n    Summary: {item.summary[:200]}"
        formatted.append(text)
    return "\n".join(formatted)
