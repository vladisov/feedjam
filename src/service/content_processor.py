"""Content processor using unified LLM service.

Replaces DataExtractor with efficient batched processing.
"""

from schemas import FeedItemIn
from service.extractor.extractor_strategy import get_extractor
from service.llm import ContentItem, LLMCache, LLMConfig, LLMService, OpenAIProvider
from utils import config
from utils.logger import get_logger

logger = get_logger(__name__)


class ContentProcessor:
    """Processes feed items with LLM-powered summarization and analysis.

    Features:
    - Batch processing for efficiency
    - Redis caching
    - Graceful degradation when LLM unavailable
    """

    def __init__(self, llm_service: LLMService | None = None):
        """Initialize processor.

        Args:
            llm_service: Optional pre-configured LLMService.
                        If None, creates one from environment config.
        """
        if llm_service:
            self.llm = llm_service
        else:
            # Create from environment config
            provider = OpenAIProvider(
                api_key=config.OPEN_AI_KEY,
                model=config.LLM_MODEL,
                embedding_model=config.LLM_EMBEDDING_MODEL,
            )
            cache = LLMCache(
                redis_url=config.REDIS_URL,
                enabled=bool(config.REDIS_URL),
            )
            llm_config = LLMConfig(
                model=config.LLM_MODEL,
                embedding_model=config.LLM_EMBEDDING_MODEL,
                batch_size=config.LLM_BATCH_SIZE,
                cache_ttl_summary=config.LLM_CACHE_TTL,
                enabled=bool(config.OPEN_AI_KEY),
            )
            self.llm = LLMService(provider, cache, llm_config)

    def process_items(self, items: list[FeedItemIn]) -> list[FeedItemIn]:
        """Process feed items: add summaries, topics, quality scores.

        Args:
            items: Feed items to process

        Returns:
            Same items with summary field populated
        """
        if not items:
            return items

        # Convert to ContentItem format
        content_items = [
            ContentItem(
                id=str(i),
                title=item.title,
                content=None,  # We'll fetch content if needed
                source_name=item.source_name,
            )
            for i, item in enumerate(items)
        ]

        # Process with LLM
        results = self.llm.process_items(content_items)

        # Update items with results
        for item, result in zip(items, results):
            if result.summary:
                item.summary = result.summary
            # Store topics and quality if the schema supports it
            # (these could be added to FeedItemIn later)

        return items

    def process_item_with_content(
        self, item: FeedItemIn, fetch_content: bool = True
    ) -> FeedItemIn:
        """Process a single item, optionally fetching full article content.

        Args:
            item: Feed item to process
            fetch_content: Whether to fetch article content first

        Returns:
            Item with summary populated
        """
        content = None
        if fetch_content and item.article_url:
            try:
                extractor = get_extractor(item.source_name)
                content = extractor(item.article_url)
            except Exception as e:
                logger.warning(f"Failed to extract content from {item.article_url}: {e}")

        content_item = ContentItem(
            id="0",
            title=item.title,
            content=content,
            source_name=item.source_name,
        )

        results = self.llm.process_items([content_item])
        if results and results[0].summary:
            item.summary = results[0].summary

        return item

    def get_embeddings(self, items: list[FeedItemIn]) -> list[list[float]]:
        """Get embeddings for feed items.

        Args:
            items: Feed items

        Returns:
            Embedding vectors for each item
        """
        texts = [f"{item.title} {item.summary or ''}" for item in items]
        hashes = [
            f"{item.title}|{item.article_url or ''}|{item.source_name}"
            for item in items
        ]

        return self.llm.get_embeddings(texts, hashes)


# Factory function for easy creation
def create_content_processor() -> ContentProcessor:
    """Create a ContentProcessor with default configuration."""
    return ContentProcessor()
