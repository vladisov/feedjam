"""Content processor using unified LLM service.

Replaces DataExtractor with efficient batched processing.
"""

from schemas import FeedItemIn
from service.extractor.extractor_strategy import get_extractor
from service.llm import ContentItem, LLMService
from utils.logger import get_logger

logger = get_logger(__name__)

# Titles longer than this will be processed by LLM to shorten them
MAX_TITLE_LENGTH = 100


class ContentProcessor:
    """Processes feed items with LLM-powered summarization and analysis.

    Features:
    - Batch processing for efficiency
    - Redis caching
    - Graceful degradation when LLM unavailable
    """

    def __init__(self, llm_service: LLMService):
        """Initialize processor.

        Args:
            llm_service: Configured LLMService instance.
        """
        self.llm = llm_service

    def process_items(self, items: list[FeedItemIn]) -> list[FeedItemIn]:
        """Process feed items: add summaries, topics, quality scores.

        Smart processing: only calls LLM if title is long or there's content to summarize.
        Items with short titles and no content are skipped to save API calls.

        Args:
            items: Feed items to process

        Returns:
            Same items with summary and cleaned title fields populated
        """
        if not items:
            return items

        # Separate items that need LLM processing
        items_to_process: list[tuple[int, FeedItemIn]] = []
        for i, item in enumerate(items):
            if self._needs_processing(item):
                items_to_process.append((i, item))

        if not items_to_process:
            logger.info("No items need LLM processing (all have short titles and no content)")
            return items

        logger.info(f"Processing {len(items_to_process)}/{len(items)} items with LLM")

        # Convert to ContentItem format
        content_items = [
            ContentItem(
                id=str(idx),
                title=item.title,
                content=item.description if item.description else None,
                source_name=item.source_name,
            )
            for idx, item in items_to_process
        ]

        # Process with LLM
        results = self.llm.process_items(content_items)

        # Update items with results
        for (_, item), result in zip(items_to_process, results, strict=True):
            if result.title:
                item.title = result.title
            if result.summary:
                item.summary = result.summary

        return items

    def _needs_processing(self, item: FeedItemIn) -> bool:
        """Check if an item needs LLM processing.

        Returns True if:
        - Title is longer than MAX_TITLE_LENGTH (needs shortening), or
        - Item has content/description to summarize
        """
        has_long_title = len(item.title) > MAX_TITLE_LENGTH
        has_content = bool(item.description and item.description.strip())
        return has_long_title or has_content

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
        if results:
            result = results[0]
            if result.title:
                item.title = result.title
            if result.summary:
                item.summary = result.summary

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
