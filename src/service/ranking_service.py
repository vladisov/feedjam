"""Ranking service for personalized feed scoring."""

import math
from collections import defaultdict
from dataclasses import dataclass

from repository.interest_storage import InterestStorage
from repository.like_history_storage import LikeHistoryStorage
from schemas.feeds import UserFeedItemIn


@dataclass
class SourceTypeConfig:
    """Configuration for how to handle popularity for a source type."""

    has_points: bool  # Whether this source type has meaningful point/vote data
    neutral_score: float = 0.5  # Score to use when no points available


# Source types that have meaningful popularity metrics
SOURCE_TYPE_CONFIGS: dict[str, SourceTypeConfig] = {
    "reddit": SourceTypeConfig(has_points=True),
    "hackernews": SourceTypeConfig(has_points=True),
    "youtube": SourceTypeConfig(has_points=True),  # views
    "github": SourceTypeConfig(has_points=True),  # stars
    "telegram": SourceTypeConfig(has_points=False),
    "twitter": SourceTypeConfig(has_points=False),
    "rss": SourceTypeConfig(has_points=False),
}

DEFAULT_SOURCE_CONFIG = SourceTypeConfig(has_points=False)


class RankingService:
    """Service for computing personalized rank scores for feed items.

    Scoring is designed to be fair across different source types:
    - Sources with points (HN, Reddit) are normalized within their type
    - Sources without points (RSS, blogs) receive a neutral popularity score
    - This prevents high-point sources from dominating the feed
    """

    # Weight configuration for score components
    INTEREST_WEIGHT = 0.4
    SOURCE_AFFINITY_WEIGHT = 0.3
    POPULARITY_WEIGHT = 0.2
    RECENCY_WEIGHT = 0.1

    def __init__(
        self,
        interest_storage: InterestStorage,
        like_history_storage: LikeHistoryStorage,
    ) -> None:
        self.interest_storage = interest_storage
        self.like_history_storage = like_history_storage

    def compute_rank_scores(
        self, user_id: int, items: list[UserFeedItemIn]
    ) -> list[UserFeedItemIn]:
        """Compute rank scores for a list of feed items.

        Scoring components:
        - interest_score: match of user topics in title/summary (40%)
        - source_affinity: historical like ratio for source (30%)
        - popularity: normalized within source type (20%)
        - recency: decay based on item age (10%)
        """
        if not items:
            return items

        # Load user preferences
        interests = self.interest_storage.get_as_map(user_id)
        source_affinities = self.like_history_storage.get_source_affinity_map(user_id)

        # Compute popularity normalizers per source type
        popularity_context = self._build_popularity_context(items)

        # Score each item
        for item in items:
            item.rank_score = self._compute_item_score(
                item, interests, source_affinities, popularity_context
            )

        # Sort by rank_score descending
        items.sort(key=lambda x: x.rank_score, reverse=True)
        return items

    def _compute_item_score(
        self,
        item: UserFeedItemIn,
        interests: dict[str, float],
        source_affinities: dict[str, float],
        popularity_context: dict[str, float],
    ) -> float:
        """Compute the combined rank score for a single item."""
        interest_score = self._compute_interest_score(item, interests)
        source_score = self._compute_source_affinity(item, source_affinities)
        popularity_score = self._compute_popularity_score(item, popularity_context)
        recency_score = self._compute_recency_score(item)

        return (
            self.INTEREST_WEIGHT * interest_score
            + self.SOURCE_AFFINITY_WEIGHT * source_score
            + self.POPULARITY_WEIGHT * popularity_score
            + self.RECENCY_WEIGHT * recency_score
        )

    # -------------------------------------------------------------------------
    # Interest scoring
    # -------------------------------------------------------------------------

    def _compute_interest_score(self, item: UserFeedItemIn, interests: dict[str, float]) -> float:
        """Compute interest score based on topic matches in title/summary.

        Returns a score in [0.0, 1.0] based on matched topics and their weights.
        """
        if not interests:
            return 0.0

        text = self._get_searchable_text(item)
        score = 0.0
        matched_count = 0

        for topic, weight in interests.items():
            if topic in text:
                score += weight
                matched_count += 1

        if matched_count > 0:
            return min(score / matched_count, 1.0)
        return 0.0

    def _get_searchable_text(self, item: UserFeedItemIn) -> str:
        """Combine item fields into searchable text."""
        parts = [item.title, item.summary or "", item.description or ""]
        return " ".join(parts).lower()

    # -------------------------------------------------------------------------
    # Source affinity scoring
    # -------------------------------------------------------------------------

    def _compute_source_affinity(
        self, item: UserFeedItemIn, source_affinities: dict[str, float]
    ) -> float:
        """Compute source affinity based on historical likes/dislikes.

        Returns a score in [0.0, 1.0], where 0.5 is neutral.
        """
        if not item.source_name:
            return 0.5

        # Affinity is in [-1, 1], convert to [0, 1]
        affinity = source_affinities.get(item.source_name, 0.0)
        return (affinity + 1.0) / 2.0

    # -------------------------------------------------------------------------
    # Popularity scoring (per-source-type normalization)
    # -------------------------------------------------------------------------

    def _build_popularity_context(self, items: list[UserFeedItemIn]) -> dict[str, float]:
        """Build max popularity values per source type for normalization.

        Returns a dict mapping source_type -> max_raw_popularity.
        This ensures items are compared fairly within their source type.
        """
        max_by_type: dict[str, float] = defaultdict(float)

        for item in items:
            source_type = self._get_source_type(item.source_name)
            config = SOURCE_TYPE_CONFIGS.get(source_type, DEFAULT_SOURCE_CONFIG)

            if config.has_points:
                raw = self._raw_popularity(item.points or 0, item.views or 0)
                max_by_type[source_type] = max(max_by_type[source_type], raw)

        # Ensure no zero denominators
        return {k: max(v, 1.0) for k, v in max_by_type.items()}

    def _compute_popularity_score(
        self, item: UserFeedItemIn, popularity_context: dict[str, float]
    ) -> float:
        """Compute normalized popularity score.

        For sources with points: normalize within source type [0.0, 1.0]
        For sources without points: return neutral score (0.5)
        """
        source_type = self._get_source_type(item.source_name)
        config = SOURCE_TYPE_CONFIGS.get(source_type, DEFAULT_SOURCE_CONFIG)

        if not config.has_points:
            return config.neutral_score

        max_popularity = popularity_context.get(source_type, 1.0)
        raw = self._raw_popularity(item.points or 0, item.views or 0)
        return raw / max_popularity

    def _raw_popularity(self, points: int, views: int) -> float:
        """Compute raw popularity using log normalization.

        Log scale reduces the impact of extreme outliers while still
        rewarding higher engagement.
        """
        return math.log1p(points) + 0.5 * math.log1p(views)

    def _get_source_type(self, source_name: str | None) -> str:
        """Extract source type from source name.

        Examples:
            'reddit-r-LocalLLaMA' -> 'reddit'
            'hackernews-best' -> 'hackernews'
            'my-blog-feed' -> 'rss'
        """
        if not source_name:
            return "rss"

        name_lower = source_name.lower()

        # Check known prefixes
        for source_type in SOURCE_TYPE_CONFIGS:
            if name_lower.startswith(source_type):
                return source_type

        # Default to RSS for unknown sources
        return "rss"

    # -------------------------------------------------------------------------
    # Recency scoring
    # -------------------------------------------------------------------------

    def _compute_recency_score(self, item: UserFeedItemIn) -> float:
        """Compute recency score based on item age.

        Returns a score in [0.0, 1.0] where newer items score higher.

        Note: Currently returns neutral 0.5 as we don't have timestamp
        in UserFeedItemIn during scoring. Items are pre-sorted by recency.
        """
        # TODO: Add created_at to UserFeedItemIn for proper recency scoring
        return 0.5
