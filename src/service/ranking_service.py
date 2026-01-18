"""Ranking service for personalized feed scoring."""

import math
from datetime import datetime, timezone

from repository.interest_storage import InterestStorage
from repository.like_history_storage import LikeHistoryStorage
from schemas.feeds import UserFeedItemIn


class RankingService:
    """Service for computing personalized rank scores for feed items."""

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
        - interest_score: substring match of user topics in title/summary
        - source_affinity: (likes - dislikes) / total for source
        - popularity: log-normalized points + views
        - recency: decay based on item age

        Combined score (configurable weights):
        score = 0.4 * interest + 0.3 * source_affinity + 0.2 * popularity + 0.1 * recency
        """
        if not items:
            return items

        # Load user data
        interests = self.interest_storage.get_as_map(user_id)
        source_affinities = self.like_history_storage.get_source_affinity_map(user_id)

        # Compute max popularity for normalization
        max_popularity = self._compute_max_popularity(items)

        # Score each item
        for item in items:
            interest_score = self._compute_interest_score(item, interests)
            source_score = self._compute_source_affinity(item, source_affinities)
            popularity_score = self._compute_popularity_score(item, max_popularity)
            recency_score = self._compute_recency_score(item)

            item.rank_score = (
                self.INTEREST_WEIGHT * interest_score
                + self.SOURCE_AFFINITY_WEIGHT * source_score
                + self.POPULARITY_WEIGHT * popularity_score
                + self.RECENCY_WEIGHT * recency_score
            )

        # Sort by rank_score descending
        items.sort(key=lambda x: x.rank_score, reverse=True)

        return items

    def _compute_interest_score(
        self, item: UserFeedItemIn, interests: dict[str, float]
    ) -> float:
        """Compute interest score based on topic matches in title/summary.

        Returns a score in [0.0, 2.0] based on matched topics and their weights.
        """
        if not interests:
            return 0.0

        # Combine title and summary for matching
        text = (item.title + " " + (item.summary or "") + " " + (item.description or "")).lower()

        score = 0.0
        matched_count = 0

        for topic, weight in interests.items():
            if topic in text:
                score += weight
                matched_count += 1

        # Normalize: return average weight of matched topics, capped at 2.0
        if matched_count > 0:
            return min(score / matched_count, 2.0)
        return 0.0

    def _compute_source_affinity(
        self, item: UserFeedItemIn, source_affinities: dict[str, float]
    ) -> float:
        """Compute source affinity score.

        Returns a score in [-1.0, 1.0] based on historical likes/dislikes for the source.
        We normalize this to [0.0, 1.0] for the final score.
        """
        if not item.source_name:
            return 0.5  # Neutral for unknown source

        affinity = source_affinities.get(item.source_name, 0.0)
        # Convert from [-1, 1] to [0, 1]
        return (affinity + 1.0) / 2.0

    def _compute_max_popularity(self, items: list[UserFeedItemIn]) -> float:
        """Compute maximum popularity value for normalization."""
        max_pop = 0.0
        for item in items:
            points = item.points or 0
            views = item.views or 0
            pop = self._raw_popularity(points, views)
            if pop > max_pop:
                max_pop = pop
        return max_pop if max_pop > 0 else 1.0

    def _raw_popularity(self, points: int, views: int) -> float:
        """Compute raw popularity using log normalization."""
        # Use log1p to handle 0 values and reduce impact of very high values
        return math.log1p(points) + 0.5 * math.log1p(views)

    def _compute_popularity_score(
        self, item: UserFeedItemIn, max_popularity: float
    ) -> float:
        """Compute normalized popularity score.

        Returns a score in [0.0, 1.0] based on points and views.
        """
        points = item.points or 0
        views = item.views or 0
        raw = self._raw_popularity(points, views)
        return raw / max_popularity

    def _compute_recency_score(self, item: UserFeedItemIn) -> float:
        """Compute recency score based on item age.

        Returns a score in [0.0, 1.0] where newer items score higher.
        Uses exponential decay with half-life of 24 hours.
        """
        # For now, we don't have creation time in UserFeedItemIn during scoring
        # Return a neutral score; items are already roughly ordered by recency
        # In a full implementation, we'd need to pass the original item's created_at
        return 0.5
