"""Request batching for LLM calls."""

from dataclasses import dataclass


@dataclass
class ContentItem:
    """Item to be processed by LLM."""

    id: str  # For matching results back
    title: str
    content: str | None = None  # Article text if available
    source_name: str = ""

    def estimated_tokens(self) -> int:
        """Rough token estimate (4 chars per token)."""
        text = f"{self.title} {self.content or ''}"
        return len(text) // 4


class RequestBatcher:
    """Batches LLM requests for efficiency."""

    def __init__(self, batch_size: int = 10, max_tokens: int = 4000):
        """Initialize batcher.

        Args:
            batch_size: Maximum items per batch
            max_tokens: Maximum estimated tokens per batch
        """
        self.batch_size = batch_size
        self.max_tokens = max_tokens

    def create_batches(self, items: list[ContentItem]) -> list[list[ContentItem]]:
        """Split items into batches respecting size and token limits.

        Args:
            items: Items to batch

        Returns:
            List of batches
        """
        if not items:
            return []

        batches = []
        current_batch: list[ContentItem] = []
        current_tokens = 0

        for item in items:
            item_tokens = item.estimated_tokens()

            # Start new batch if limits exceeded
            should_start_new = len(current_batch) >= self.batch_size or (
                current_tokens + item_tokens > self.max_tokens and current_batch
            )

            if should_start_new:
                batches.append(current_batch)
                current_batch = []
                current_tokens = 0

            current_batch.append(item)
            current_tokens += item_tokens

        # Don't forget the last batch
        if current_batch:
            batches.append(current_batch)

        return batches

    def create_embedding_batches(
        self, texts: list[str], max_per_batch: int = 100
    ) -> list[list[str]]:
        """Batch texts for embedding API (typically allows larger batches).

        Args:
            texts: Texts to embed
            max_per_batch: Maximum texts per batch (OpenAI limit is ~2048)

        Returns:
            List of text batches
        """
        if not texts:
            return []

        return [texts[i : i + max_per_batch] for i in range(0, len(texts), max_per_batch)]
