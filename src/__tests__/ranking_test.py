"""Tests for the ranking service."""

from __tests__.base import BaseTestCase
from schemas import UserInterestIn
from schemas.feeds import ItemState, UserFeedItemIn
from service.ranking_service import RankingService


class TestRankingService(BaseTestCase):
    """Test ranking service functionality."""

    def _create_feed_item(
        self,
        title: str,
        source_name: str = "test_source",
        points: int = 0,
        views: int = 0,
        summary: str | None = None,
    ) -> UserFeedItemIn:
        """Create a test feed item."""
        return UserFeedItemIn(
            feed_item_id=1,
            user_id=1,
            title=title,
            source_name=source_name,
            state=ItemState(),
            description="",
            points=points,
            views=views,
            summary=summary,
        )

    def test_interest_score_matches_topic_in_title(self):
        """Test that interest topics are matched in title."""
        user = self.create_user_direct("test")

        # Add interests
        self.interest_storage.create(user.id, UserInterestIn(topic="python", weight=1.5))

        items = [
            self._create_feed_item("Learning Python for beginners"),
            self._create_feed_item("Introduction to JavaScript"),
        ]

        ranked = self.ranking_service.compute_rank_scores(user.id, items)

        # Python item should rank higher
        assert ranked[0].title == "Learning Python for beginners"
        assert ranked[0].rank_score > ranked[1].rank_score

    def test_interest_score_matches_topic_in_summary(self):
        """Test that interest topics are matched in summary."""
        user = self.create_user_direct("test")

        self.interest_storage.create(user.id, UserInterestIn(topic="rust", weight=2.0))

        items = [
            self._create_feed_item("New programming language", summary="Rust is fast"),
            self._create_feed_item("Another article", summary="JavaScript tips"),
        ]

        ranked = self.ranking_service.compute_rank_scores(user.id, items)

        assert ranked[0].summary == "Rust is fast"
        assert ranked[0].rank_score > ranked[1].rank_score

    def test_interest_weight_affects_score(self):
        """Test that higher weight gives higher score."""
        user = self.create_user_direct("test")

        self.interest_storage.create(user.id, UserInterestIn(topic="python", weight=2.0))
        self.interest_storage.create(user.id, UserInterestIn(topic="java", weight=0.5))

        items = [
            self._create_feed_item("Python tutorial"),
            self._create_feed_item("Java tutorial"),
        ]

        ranked = self.ranking_service.compute_rank_scores(user.id, items)

        # Python (weight 2.0) should rank higher than Java (weight 0.5)
        assert ranked[0].title == "Python tutorial"

    def test_source_affinity_affects_ranking(self):
        """Test that liked sources rank higher."""
        user = self.create_user_direct("test")

        # Simulate like history: source_a has good affinity, source_b has bad
        self.like_history_storage.increment_like(user.id, "source_a")
        self.like_history_storage.increment_like(user.id, "source_a")
        self.like_history_storage.increment_dislike(user.id, "source_b")
        self.like_history_storage.increment_dislike(user.id, "source_b")

        items = [
            self._create_feed_item("Article from liked source", source_name="source_a"),
            self._create_feed_item("Article from disliked source", source_name="source_b"),
        ]

        ranked = self.ranking_service.compute_rank_scores(user.id, items)

        assert ranked[0].source_name == "source_a"
        assert ranked[0].rank_score > ranked[1].rank_score

    def test_popularity_affects_ranking(self):
        """Test that items with more points/views rank higher."""
        user = self.create_user_direct("test")

        items = [
            self._create_feed_item("Popular article", points=1000, views=5000),
            self._create_feed_item("Unpopular article", points=10, views=50),
        ]

        ranked = self.ranking_service.compute_rank_scores(user.id, items)

        assert ranked[0].title == "Popular article"
        assert ranked[0].rank_score > ranked[1].rank_score

    def test_combined_factors(self):
        """Test ranking with multiple factors combined."""
        user = self.create_user_direct("test")

        # Add interest in "python"
        self.interest_storage.create(user.id, UserInterestIn(topic="python", weight=1.5))

        # Add source affinity for "good_source"
        self.like_history_storage.increment_like(user.id, "good_source")

        items = [
            # High interest match + good source + high popularity
            self._create_feed_item(
                "Python best practices",
                source_name="good_source",
                points=500,
                views=1000,
            ),
            # No interest match + neutral source + low popularity
            self._create_feed_item(
                "Random article",
                source_name="neutral_source",
                points=10,
                views=20,
            ),
        ]

        ranked = self.ranking_service.compute_rank_scores(user.id, items)

        assert ranked[0].title == "Python best practices"
        # Score should be significantly higher
        assert ranked[0].rank_score > ranked[1].rank_score * 1.5

    def test_empty_items_returns_empty(self):
        """Test that empty input returns empty output."""
        user = self.create_user_direct("test")
        ranked = self.ranking_service.compute_rank_scores(user.id, [])
        assert ranked == []

    def test_no_interests_still_ranks_by_other_factors(self):
        """Test ranking works when user has no interests."""
        user = self.create_user_direct("test")

        items = [
            self._create_feed_item("High popularity", points=1000),
            self._create_feed_item("Low popularity", points=10),
        ]

        ranked = self.ranking_service.compute_rank_scores(user.id, items)

        # Should still rank by popularity
        assert ranked[0].title == "High popularity"


class TestSourceAffinityMap(BaseTestCase):
    """Test like history storage affinity calculations."""

    def test_affinity_all_likes(self):
        """Test affinity is 1.0 when all interactions are likes."""
        user = self.create_user_direct("test")

        self.like_history_storage.increment_like(user.id, "source_a")
        self.like_history_storage.increment_like(user.id, "source_a")
        self.like_history_storage.increment_like(user.id, "source_a")

        affinities = self.like_history_storage.get_source_affinity_map(user.id)

        assert affinities["source_a"] == 1.0

    def test_affinity_all_dislikes(self):
        """Test affinity is -1.0 when all interactions are dislikes."""
        user = self.create_user_direct("test")

        self.like_history_storage.increment_dislike(user.id, "source_a")
        self.like_history_storage.increment_dislike(user.id, "source_a")

        affinities = self.like_history_storage.get_source_affinity_map(user.id)

        assert affinities["source_a"] == -1.0

    def test_affinity_mixed(self):
        """Test affinity with mixed likes/dislikes."""
        user = self.create_user_direct("test")

        # 3 likes, 1 dislike = (3-1)/4 = 0.5
        self.like_history_storage.increment_like(user.id, "source_a")
        self.like_history_storage.increment_like(user.id, "source_a")
        self.like_history_storage.increment_like(user.id, "source_a")
        self.like_history_storage.increment_dislike(user.id, "source_a")

        affinities = self.like_history_storage.get_source_affinity_map(user.id)

        assert affinities["source_a"] == 0.5

    def test_no_history_returns_empty(self):
        """Test empty affinity map when no history."""
        user = self.create_user_direct("test")

        affinities = self.like_history_storage.get_source_affinity_map(user.id)

        assert affinities == {}


class TestInterestStorage(BaseTestCase):
    """Test interest storage operations."""

    def test_create_and_get_interest(self):
        """Test creating and retrieving interests."""
        user = self.create_user_direct("test")

        interest = self.interest_storage.create(
            user.id, UserInterestIn(topic="python", weight=1.5)
        )

        assert interest.topic == "python"
        assert interest.weight == 1.5
        assert interest.user_id == user.id

    def test_get_interests_by_user(self):
        """Test getting all interests for a user."""
        user = self.create_user_direct("test")

        self.interest_storage.create(user.id, UserInterestIn(topic="python", weight=1.0))
        self.interest_storage.create(user.id, UserInterestIn(topic="rust", weight=1.5))

        interests = self.interest_storage.get_by_user(user.id)

        assert len(interests) == 2
        topics = {i.topic for i in interests}
        assert topics == {"python", "rust"}

    def test_replace_all_interests(self):
        """Test bulk replacing interests."""
        user = self.create_user_direct("test")

        # Create initial interests
        self.interest_storage.create(user.id, UserInterestIn(topic="old_topic", weight=1.0))

        # Replace with new ones
        new_interests = [
            UserInterestIn(topic="new_topic_1", weight=1.0),
            UserInterestIn(topic="new_topic_2", weight=2.0),
        ]
        result = self.interest_storage.replace_all(user.id, new_interests)

        assert len(result) == 2
        topics = {i.topic for i in result}
        assert topics == {"new_topic_1", "new_topic_2"}

        # Old topic should be gone
        all_interests = self.interest_storage.get_by_user(user.id)
        assert len(all_interests) == 2

    def test_get_as_map(self):
        """Test getting interests as topic->weight map."""
        user = self.create_user_direct("test")

        self.interest_storage.create(user.id, UserInterestIn(topic="Python", weight=1.5))
        self.interest_storage.create(user.id, UserInterestIn(topic="RUST", weight=2.0))

        interest_map = self.interest_storage.get_as_map(user.id)

        # Should be lowercase
        assert interest_map == {"python": 1.5, "rust": 2.0}

    def test_delete_interest(self):
        """Test deleting an interest."""
        user = self.create_user_direct("test")

        interest = self.interest_storage.create(
            user.id, UserInterestIn(topic="python", weight=1.0)
        )

        result = self.interest_storage.delete(interest.id)
        assert result is True

        interests = self.interest_storage.get_by_user(user.id)
        assert len(interests) == 0
