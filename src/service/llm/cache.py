"""Redis caching for LLM responses."""

import hashlib
import json

import redis

from utils.logger import get_logger

logger = get_logger(__name__)


def content_hash(title: str, url: str | None, source_name: str) -> str:
    """Compute stable hash for cache keys."""
    content = f"{title}|{url or ''}|{source_name}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


class LLMCache:
    """Redis cache for LLM responses."""

    # Cache key prefixes
    PREFIX_SUMMARY = "llm:summary"
    PREFIX_EMBEDDING = "llm:emb"
    PREFIX_QUALITY = "llm:quality"
    PREFIX_TOPICS = "llm:topics"
    PREFIX_RELEVANCE = "llm:rel"
    PREFIX_PROCESSED = "llm:processed"  # Combined summary+quality+topics

    def __init__(self, redis_url: str, enabled: bool = True):
        self.enabled = enabled
        self._client: redis.Redis | None = None

        if enabled:
            try:
                self._client = redis.from_url(redis_url, decode_responses=True)
                self._client.ping()
                logger.info("LLM cache connected to Redis")
            except redis.ConnectionError as e:
                logger.warning(f"Redis connection failed, caching disabled: {e}")
                self._client = None
                self.enabled = False

    @property
    def client(self) -> redis.Redis | None:
        return self._client

    def _key(self, prefix: str, *parts: str) -> str:
        """Build cache key from prefix and parts."""
        return f"{prefix}:{':'.join(parts)}"

    # --- Processed content (combined summary + quality + topics) ---

    def get_processed(self, content_hash: str) -> dict | None:
        """Get processed content from cache."""
        if not self.enabled or not self._client:
            return None

        try:
            key = self._key(self.PREFIX_PROCESSED, content_hash)
            data = self._client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        return None

    def set_processed(self, content_hash: str, data: dict, ttl: int) -> None:
        """Cache processed content."""
        if not self.enabled or not self._client:
            return

        try:
            key = self._key(self.PREFIX_PROCESSED, content_hash)
            self._client.setex(key, ttl, json.dumps(data))
        except Exception as e:
            logger.warning(f"Cache set error: {e}")

    # --- Embeddings ---

    def get_embedding(self, content_hash: str) -> list[float] | None:
        """Get embedding from cache."""
        if not self.enabled or not self._client:
            return None

        try:
            key = self._key(self.PREFIX_EMBEDDING, content_hash)
            data = self._client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        return None

    def set_embedding(self, content_hash: str, embedding: list[float], ttl: int) -> None:
        """Cache embedding."""
        if not self.enabled or not self._client:
            return

        try:
            key = self._key(self.PREFIX_EMBEDDING, content_hash)
            self._client.setex(key, ttl, json.dumps(embedding))
        except Exception as e:
            logger.warning(f"Cache set error: {e}")

    def get_embeddings_batch(self, hashes: list[str]) -> dict[str, list[float] | None]:
        """Get multiple embeddings from cache."""
        if not self.enabled or not self._client or not hashes:
            return {h: None for h in hashes}

        try:
            keys = [self._key(self.PREFIX_EMBEDDING, h) for h in hashes]
            values = self._client.mget(keys)
            return {
                h: json.loads(v) if v else None
                for h, v in zip(hashes, values, strict=False)
            }
        except Exception as e:
            logger.warning(f"Cache mget error: {e}")
            return {h: None for h in hashes}

    # --- User-specific relevance scores ---

    def get_relevance(self, user_id: int, content_hash: str) -> float | None:
        """Get relevance score from cache."""
        if not self.enabled or not self._client:
            return None

        try:
            key = self._key(self.PREFIX_RELEVANCE, str(user_id), content_hash)
            data = self._client.get(key)
            if data:
                return float(data)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        return None

    def set_relevance(self, user_id: int, content_hash: str, score: float, ttl: int) -> None:
        """Cache relevance score."""
        if not self.enabled or not self._client:
            return

        try:
            key = self._key(self.PREFIX_RELEVANCE, str(user_id), content_hash)
            self._client.setex(key, ttl, str(score))
        except Exception as e:
            logger.warning(f"Cache set error: {e}")

    # --- Batch operations ---

    def get_processed_batch(self, hashes: list[str]) -> dict[str, dict | None]:
        """Get multiple processed contents from cache."""
        if not self.enabled or not self._client or not hashes:
            return {h: None for h in hashes}

        try:
            keys = [self._key(self.PREFIX_PROCESSED, h) for h in hashes]
            values = self._client.mget(keys)
            return {
                h: json.loads(v) if v else None
                for h, v in zip(hashes, values, strict=False)
            }
        except Exception as e:
            logger.warning(f"Cache mget error: {e}")
            return {h: None for h in hashes}

    def set_processed_batch(self, items: dict[str, dict], ttl: int) -> None:
        """Cache multiple processed contents."""
        if not self.enabled or not self._client or not items:
            return

        try:
            pipe = self._client.pipeline()
            for content_hash, data in items.items():
                key = self._key(self.PREFIX_PROCESSED, content_hash)
                pipe.setex(key, ttl, json.dumps(data))
            pipe.execute()
        except Exception as e:
            logger.warning(f"Cache batch set error: {e}")
