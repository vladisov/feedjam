# Personalized Feed Ranking

FeedJam uses a personalized ranking algorithm to order feed items based on user preferences and behavior.

## Overview

The ranking system considers four factors when scoring items:

| Factor | Weight | Description |
|--------|--------|-------------|
| Interest Match | 40% | How well the item matches user-defined topics |
| Source Affinity | 30% | Historical like/dislike ratio for the source |
| Popularity | 20% | Points and views (log-normalized) |
| Recency | 10% | How recently the item was published |

## Scoring Components

### 1. Interest Score (0.0 - 2.0)

Users define topics they're interested in (e.g., "python", "rust", "machine-learning") with a weight multiplier:

| Weight | Label | Effect |
|--------|-------|--------|
| 0.5 | Low | Slight boost |
| 1.0 | Normal | Standard boost |
| 1.5 | High | Strong boost |
| 2.0 | Very High | Maximum boost |

The algorithm performs substring matching against the item's title, summary, and description. The score is the average weight of all matched topics.

**Example:**
- User interests: `python (1.5x)`, `fastapi (2.0x)`
- Item title: "Building APIs with FastAPI and Python"
- Matches: `python`, `fastapi`
- Interest score: `(1.5 + 2.0) / 2 = 1.75`

### 2. Source Affinity (-1.0 to 1.0, normalized to 0.0 - 1.0)

Tracks user engagement with sources based on like/dislike history:

```
affinity = (likes - dislikes) / total_interactions
```

| Scenario | Affinity | Normalized |
|----------|----------|------------|
| All likes | 1.0 | 1.0 |
| Equal likes/dislikes | 0.0 | 0.5 |
| All dislikes | -1.0 | 0.0 |
| No history | 0.0 | 0.5 |

**Example:**
- Source "Hacker News": 8 likes, 2 dislikes
- Affinity: `(8 - 2) / 10 = 0.6`
- Normalized: `(0.6 + 1.0) / 2 = 0.8`

### 3. Popularity Score (0.0 - 1.0)

Uses log-normalization to reduce the impact of outliers:

```python
raw_popularity = log(1 + points) + 0.5 * log(1 + views)
score = raw_popularity / max_popularity_in_batch
```

This ensures items with extremely high points don't completely dominate, while still rewarding popular content.

### 4. Recency Score (0.0 - 1.0)

Currently returns a neutral value (0.5) as items are already roughly ordered by time during feed generation. Future enhancement: exponential decay with 24-hour half-life.

## Final Score Calculation

```python
score = (0.4 * interest_score +
         0.3 * source_affinity +
         0.2 * popularity_score +
         0.1 * recency_score)
```

Items are sorted by `rank_score` in descending order.

## When Ranking is Applied

Ranking happens at **feed generation time**, not query time:

1. User requests feed regeneration (via subscription run or manual refresh)
2. System collects new items from subscribed sources
3. RankingService computes `rank_score` for each item
4. Items are stored with their scores in `user_feed_items.rank_score`
5. Feed queries return items sorted by `rank_score DESC`

This approach:
- Avoids expensive computation on every read
- Allows scores to be pre-computed during async jobs
- Provides consistent ordering across page loads

## API Endpoints

### Managing Interests

```bash
# List interests
GET /users/{user_id}/interests

# Add single interest
POST /users/{user_id}/interests
{"topic": "python", "weight": 1.5}

# Replace all interests (bulk update)
PUT /users/{user_id}/interests
{"interests": [{"topic": "python", "weight": 1.5}, {"topic": "rust", "weight": 1.0}]}

# Delete interest
DELETE /users/{user_id}/interests/{interest_id}
```

### Like/Dislike Items

```bash
# Toggle like (updates source affinity)
POST /feed/{user_id}/items/{item_id}/like

# Toggle dislike (updates source affinity)
POST /feed/{user_id}/items/{item_id}/dislike
```

## Database Schema

### user_interests
| Column | Type | Description |
|--------|------|-------------|
| id | int | Primary key |
| user_id | int | FK to users |
| topic | varchar(100) | Interest keyword |
| weight | float | Priority multiplier (0.0-2.0) |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

### user_like_history
| Column | Type | Description |
|--------|------|-------------|
| id | int | Primary key |
| user_id | int | FK to users |
| source_name | varchar(255) | Aggregated source identifier |
| like_count | int | Total likes for this source |
| dislike_count | int | Total dislikes for this source |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

### user_feed_items (updated)
| Column | Type | Description |
|--------|------|-------------|
| rank_score | float | Computed ranking score (default 0.0) |

## Tuning the Algorithm

Weights are defined as class constants in `RankingService`:

```python
class RankingService:
    INTEREST_WEIGHT = 0.4
    SOURCE_AFFINITY_WEIGHT = 0.3
    POPULARITY_WEIGHT = 0.2
    RECENCY_WEIGHT = 0.1
```

Adjust these values to change the ranking behavior:
- Increase `INTEREST_WEIGHT` to prioritize topic matches
- Increase `SOURCE_AFFINITY_WEIGHT` to favor sources user likes
- Increase `POPULARITY_WEIGHT` to surface trending content
- Increase `RECENCY_WEIGHT` to prefer newer items

## Future Enhancements

- **Recency decay**: Implement exponential time-based decay
- **Keyword extraction**: Use NLP to extract topics from content
- **Collaborative filtering**: Learn from similar users' preferences
- **A/B testing**: Compare ranking strategies with metrics
- **Per-source weights**: Allow users to boost/mute specific sources
