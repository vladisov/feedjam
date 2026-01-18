"""Unified LLM service for all AI operations."""

from service.llm.batcher import ContentItem, RequestBatcher
from service.llm.cache import LLMCache, content_hash
from service.llm.config import LLMConfig, ProcessedContent
from service.llm.prompts import (
    PROCESS_ITEMS_PROMPT,
    SCORE_RELEVANCE_PROMPT,
    SYSTEM_CONTENT_PROCESSOR,
    SYSTEM_RELEVANCE_SCORER,
    format_items_for_processing,
    format_items_for_relevance,
)
from service.llm.provider import LLMProvider
from utils.logger import get_logger

logger = get_logger(__name__)


class LLMService:
    """Unified service for all LLM operations.

    Handles:
    - Content processing (summarization, topic extraction, quality scoring)
    - Embeddings
    - Relevance scoring

    Features:
    - Batching for efficiency
    - Redis caching
    - Graceful degradation
    """

    def __init__(
        self,
        provider: LLMProvider,
        cache: LLMCache,
        config: LLMConfig | None = None,
    ):
        self.provider = provider
        self.cache = cache
        self.config = config or LLMConfig()
        self.batcher = RequestBatcher(
            batch_size=self.config.batch_size,
            max_tokens=self.config.max_tokens_per_batch,
        )

    def process_items(self, items: list[ContentItem]) -> list[ProcessedContent]:
        """Process items: summarize, extract topics, score quality.

        Checks cache first, only processes uncached items.

        Args:
            items: Items to process

        Returns:
            ProcessedContent for each item (in same order)
        """
        if not items or not self.config.enabled:
            return [ProcessedContent() for _ in items]

        # Compute hashes and check cache
        item_hashes = [
            content_hash(item.title, None, item.source_name) for item in items
        ]
        cached = self.cache.get_processed_batch(item_hashes)

        # Separate cached vs uncached
        results: dict[str, ProcessedContent] = {}
        uncached_items: list[tuple[int, ContentItem, str]] = []

        for i, (item, h) in enumerate(zip(items, item_hashes)):
            if cached.get(h):
                results[h] = ProcessedContent.from_dict(cached[h])
            else:
                uncached_items.append((i, item, h))

        # Process uncached items in batches
        if uncached_items:
            logger.info(f"Processing {len(uncached_items)} uncached items")
            uncached_content = [item for _, item, _ in uncached_items]
            uncached_hashes = [h for _, _, h in uncached_items]

            processed = self._process_batch(uncached_content)

            # Cache results
            to_cache = {}
            for h, result in zip(uncached_hashes, processed):
                results[h] = result
                to_cache[h] = result.to_dict()

            self.cache.set_processed_batch(to_cache, self.config.cache_ttl_summary)

        # Return in original order
        return [results[h] for h in item_hashes]

    def _process_batch(self, items: list[ContentItem]) -> list[ProcessedContent]:
        """Process a batch of items with LLM."""
        all_results: list[ProcessedContent] = []

        for batch in self.batcher.create_batches(items):
            try:
                batch_results = self._call_process_llm(batch)
                all_results.extend(batch_results)
            except Exception as e:
                logger.warning(f"LLM processing failed: {e}, using fallbacks")
                all_results.extend([ProcessedContent() for _ in batch])

        return all_results

    def _call_process_llm(self, items: list[ContentItem]) -> list[ProcessedContent]:
        """Make LLM call for content processing."""
        prompt = PROCESS_ITEMS_PROMPT.format(
            items=format_items_for_processing(items),
            count=len(items),
        )

        response = self.provider.complete(
            prompt=prompt,
            system=SYSTEM_CONTENT_PROCESSOR,
            response_format="json",
            max_tokens=self.config.max_completion_tokens,
            temperature=self.config.temperature,
        )

        results = response.get("results", [])

        # Parse results, with fallbacks for malformed responses
        processed = []
        for i, item in enumerate(items):
            if i < len(results):
                r = results[i]
                processed.append(
                    ProcessedContent(
                        title=r.get("title"),  # None if LLM says original is fine
                        summary=r.get("summary"),
                        topics=r.get("topics", []),
                        quality_score=float(r.get("quality", 0.5)),
                    )
                )
            else:
                logger.warning(f"Missing result for item {i}: {item.title}")
                processed.append(ProcessedContent())

        return processed

    def get_embeddings(
        self, texts: list[str], content_hashes: list[str] | None = None
    ) -> list[list[float]]:
        """Get embeddings for texts (cached if hashes provided).

        Args:
            texts: Texts to embed
            content_hashes: Optional hashes for caching

        Returns:
            List of embedding vectors
        """
        if not texts or not self.config.enabled:
            return [[] for _ in texts]

        # Check cache if hashes provided
        if content_hashes and self.cache.enabled:
            cached = self.cache.get_embeddings_batch(content_hashes)
            results: list[list[float] | None] = [cached.get(h) for h in content_hashes]

            # Find uncached
            uncached_indices = [i for i, r in enumerate(results) if r is None]
            if not uncached_indices:
                return [r if r else [] for r in results]

            # Get uncached embeddings
            uncached_texts = [texts[i] for i in uncached_indices]
            uncached_embeddings = self._get_embeddings_batch(uncached_texts)

            # Fill in results and cache
            for idx, emb in zip(uncached_indices, uncached_embeddings):
                results[idx] = emb
                h = content_hashes[idx]
                self.cache.set_embedding(h, emb, self.config.cache_ttl_embedding)

            return [r if r else [] for r in results]

        # No caching, just get embeddings
        return self._get_embeddings_batch(texts)

    def _get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings in batches."""
        all_embeddings: list[list[float]] = []

        for batch in self.batcher.create_embedding_batches(texts):
            try:
                embeddings = self.provider.get_embeddings(batch)
                all_embeddings.extend(embeddings)
            except Exception as e:
                logger.warning(f"Embedding failed: {e}, using empty vectors")
                all_embeddings.extend([[] for _ in batch])

        return all_embeddings

    def score_relevance(
        self,
        items: list,
        interests: dict[str, float],
        liked_sources: list[str] | None = None,
    ) -> list[float]:
        """Score items for user relevance using LLM.

        Args:
            items: Items to score (must have title, optionally source_name, summary)
            interests: User interests {topic: weight}
            liked_sources: Sources the user has liked

        Returns:
            Relevance scores (0.0-1.0) for each item
        """
        if not items or not self.config.enabled or not interests:
            return [0.5] * len(items)

        try:
            return self._call_relevance_llm(items, interests, liked_sources or [])
        except Exception as e:
            logger.warning(f"Relevance scoring failed: {e}, using neutral scores")
            return [0.5] * len(items)

    def _call_relevance_llm(
        self,
        items: list,
        interests: dict[str, float],
        liked_sources: list[str],
    ) -> list[float]:
        """Make LLM call for relevance scoring."""
        # Format interests with weights
        interest_str = ", ".join(
            f"{topic} ({weight}x)" for topic, weight in interests.items()
        )

        prompt = SCORE_RELEVANCE_PROMPT.format(
            interests=interest_str,
            liked_sources=", ".join(liked_sources) if liked_sources else "None",
            items=format_items_for_relevance(items),
            count=len(items),
        )

        response = self.provider.complete(
            prompt=prompt,
            system=SYSTEM_RELEVANCE_SCORER,
            response_format="json",
            max_tokens=500,
            temperature=0.2,
        )

        scores = response.get("scores", [])

        # Ensure we have the right number of scores
        result = []
        for i in range(len(items)):
            if i < len(scores):
                try:
                    score = float(scores[i])
                    result.append(max(0.0, min(1.0, score)))  # Clamp to [0, 1]
                except (ValueError, TypeError):
                    result.append(0.5)
            else:
                result.append(0.5)

        return result
