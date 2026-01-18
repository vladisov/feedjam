"""LLM service configuration."""

from dataclasses import dataclass, field


@dataclass
class LLMConfig:
    """Configuration for LLM service."""

    # Model settings
    model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    # Batching
    batch_size: int = 10
    max_tokens_per_batch: int = 4000

    # Cache TTLs (seconds)
    cache_ttl_summary: int = 604800  # 7 days
    cache_ttl_embedding: int = 2592000  # 30 days
    cache_ttl_quality: int = 604800  # 7 days
    cache_ttl_relevance: int = 3600  # 1 hour

    # Completion settings
    max_completion_tokens: int = 2000
    temperature: float = 0.3

    # Feature flags
    enabled: bool = True
    cache_enabled: bool = True


@dataclass
class ProcessedContent:
    """Result of LLM content processing."""

    title: str | None = None  # Cleaned/shortened title (if original was long)
    summary: str | None = None
    topics: list[str] = field(default_factory=list)
    quality_score: float = 0.5

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "summary": self.summary,
            "topics": self.topics,
            "quality_score": self.quality_score,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProcessedContent":
        return cls(
            title=data.get("title"),
            summary=data.get("summary"),
            topics=data.get("topics", []),
            quality_score=data.get("quality_score", 0.5),
        )
