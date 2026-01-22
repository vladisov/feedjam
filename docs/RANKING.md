# Personalized Feed Ranking

FeedJam uses a personalized ranking algorithm to order feed items based on user preferences and behavior.

## Overview

The ranking system considers four factors when scoring items:

| Factor | Weight | Description |
|--------|--------|-------------|
| Interest Match | 40% | How well the item matches user-defined topics |
| Source Affinity | 30% | Historical like/hide ratio for the source |
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

Tracks user engagement with sources based on like/hide history:

```
affinity = (likes - hides) / total_interactions
```

| Scenario | Affinity | Normalized |
|----------|----------|------------|
| All likes | 1.0 | 1.0 |
| Equal likes/hides | 0.0 | 0.5 |
| All hides | -1.0 | 0.0 |
| No history | 0.0 | 0.5 |

**Example:**
- Source "Hacker News": 8 likes, 2 hides
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

### Like/Hide Items

```bash
# Toggle like (updates source affinity positively)
POST /feed/{user_id}/items/{item_id}/like

# Toggle hide (updates source affinity negatively)
POST /feed/{user_id}/items/{item_id}/hide
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
| hide_count | int | Total hides for this source (negative signal) |
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

## Extensible Architecture (Planned)

The ranking system is designed to be extensible with a pluggable scorer architecture. This allows adding new scoring methods (including LLM-powered ones) without modifying core logic.

### Scorer Interface

Each scorer implements a simple interface:

```python
class BaseScorer(ABC):
    """Base class for all ranking scorers."""

    name: str  # Unique identifier
    weight: float  # Default weight in final score

    @abstractmethod
    def score(self, item: UserFeedItemIn, context: ScoringContext) -> float:
        """Return a score in [0.0, 1.0] for the item."""
        pass

    @abstractmethod
    def score_batch(self, items: list[UserFeedItemIn], context: ScoringContext) -> list[float]:
        """Score multiple items (for efficiency with LLM calls)."""
        pass
```

### ScoringContext

Shared context passed to all scorers:

```python
@dataclass
class ScoringContext:
    user_id: int
    interests: dict[str, float]  # topic -> weight
    source_affinities: dict[str, float]  # source -> affinity
    user_profile: UserProfile | None  # Extended profile for LLM
    config: ScoringConfig  # Runtime configuration
```

### Planned Scorers

| Scorer | Type | Description |
|--------|------|-------------|
| `InterestScorer` | Rule-based | Current keyword matching (exists) |
| `SourceAffinityScorer` | Rule-based | Current like/dislike ratio (exists) |
| `PopularityScorer` | Rule-based | Current log-normalized points (exists) |
| `RecencyScorer` | Rule-based | Time decay scoring (exists) |
| `SemanticScorer` | LLM | Embedding similarity with user interests |
| `RelevanceScorer` | LLM | LLM judges relevance to user profile |
| `QualityScorer` | LLM | LLM evaluates content quality |
| `NoveltyScorer` | LLM | Detects novel vs. repetitive content |

### LLM Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│                     RankingService                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ InterestScore│  │SourceAffinity│  │ PopularityS. │      │
│  │  (rule-based)│  │  (rule-based) │  │  (rule-based)│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │SemanticScorer│  │RelevanceScor.│  │ QualityScorer│      │
│  │    (LLM)     │  │    (LLM)     │  │    (LLM)     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │               │
│         └─────────────────┼─────────────────┘               │
│                           ▼                                 │
│                   ┌──────────────┐                          │
│                   │  LLMProvider │                          │
│                   │ (OpenAI/etc) │                          │
│                   └──────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

### LLM Scorer Examples

#### SemanticScorer (Embeddings)

Uses vector embeddings to find semantic similarity between items and user interests:

```python
class SemanticScorer(BaseScorer):
    """Score items by semantic similarity to user interests."""

    name = "semantic"
    weight = 0.3

    def __init__(self, embedding_provider: EmbeddingProvider):
        self.embeddings = embedding_provider

    def score_batch(self, items: list[UserFeedItemIn], ctx: ScoringContext) -> list[float]:
        # Get user interest embedding (cached)
        user_embedding = self.embeddings.get_interest_embedding(ctx.interests)

        # Get item embeddings (batched for efficiency)
        item_texts = [f"{i.title} {i.summary or ''}" for i in items]
        item_embeddings = self.embeddings.get_batch(item_texts)

        # Cosine similarity
        return [cosine_similarity(user_embedding, emb) for emb in item_embeddings]
```

#### RelevanceScorer (LLM Judge)

Uses LLM to directly judge relevance:

```python
class RelevanceScorer(BaseScorer):
    """LLM judges item relevance to user profile."""

    name = "relevance"
    weight = 0.25

    def score_batch(self, items: list[UserFeedItemIn], ctx: ScoringContext) -> list[float]:
        prompt = f"""
        User interests: {', '.join(ctx.interests.keys())}
        User liked sources: {', '.join(ctx.liked_sources)}

        Rate each item's relevance (0.0-1.0):
        {self._format_items(items)}

        Return JSON: {{"scores": [0.8, 0.3, ...]}}
        """

        response = self.llm.complete(prompt, response_format="json")
        return response["scores"]
```

#### QualityScorer (Content Quality)

Evaluates content quality independent of user preferences:

```python
class QualityScorer(BaseScorer):
    """LLM evaluates content quality."""

    name = "quality"
    weight = 0.15

    def score_batch(self, items: list[UserFeedItemIn], ctx: ScoringContext) -> list[float]:
        prompt = """
        Rate each item's quality (0.0-1.0) based on:
        - Informativeness
        - Writing clarity
        - Substance vs clickbait

        Items:
        {items}

        Return JSON: {{"scores": [...]}}
        """
        # ...
```

### Configuration

Weights configurable per-user or globally:

```python
# Default scoring config
SCORING_CONFIG = {
    "scorers": {
        "interest": {"enabled": True, "weight": 0.25},
        "source_affinity": {"enabled": True, "weight": 0.20},
        "popularity": {"enabled": True, "weight": 0.15},
        "recency": {"enabled": True, "weight": 0.10},
        "semantic": {"enabled": True, "weight": 0.15},  # LLM
        "relevance": {"enabled": True, "weight": 0.10},  # LLM
        "quality": {"enabled": True, "weight": 0.05},    # LLM
    },
    "llm": {
        "provider": "openai",
        "model": "gpt-4o-mini",  # Fast, cheap for scoring
        "batch_size": 20,
        "cache_ttl": 3600,
    }
}
```

### Caching Strategy

LLM calls are expensive. Caching is critical:

| Cache Level | TTL | What's Cached |
|-------------|-----|---------------|
| User embeddings | 1 hour | Embedding of user interests |
| Item embeddings | 24 hours | Embedding of item title+summary |
| Quality scores | 24 hours | LLM quality assessment (user-independent) |
| Relevance scores | 1 hour | User-specific relevance (per user+item) |

```python
# Redis cache keys
user_embedding:{user_id} -> vector
item_embedding:{item_hash} -> vector
quality_score:{item_hash} -> float
relevance_score:{user_id}:{item_hash} -> float
```

### Graceful Degradation

LLM scorers fail gracefully:

```python
class LLMScorer(BaseScorer):
    def score_batch(self, items, ctx):
        try:
            return self._llm_score(items, ctx)
        except (RateLimitError, TimeoutError, APIError) as e:
            logger.warning(f"LLM scorer {self.name} failed: {e}")
            return [0.5] * len(items)  # Neutral fallback
```

### Implementation Order

1. **Phase 1: Refactor** (Current)
   - Extract current scoring logic into separate scorer classes
   - Add scorer registry and plugin system
   - Add `ScoringContext` dataclass

2. **Phase 2: Embeddings**
   - Add `EmbeddingProvider` abstraction
   - Implement `SemanticScorer` with OpenAI embeddings
   - Add Redis caching for embeddings

3. **Phase 3: LLM Scoring**
   - Add `LLMProvider` abstraction
   - Implement `RelevanceScorer` and `QualityScorer`
   - Add batching and rate limiting

4. **Phase 4: Personalization**
   - Per-user weight configuration
   - A/B testing framework
   - Feedback loop (did user engage with highly-ranked items?)

### File Structure (Planned)

```
src/service/ranking/
├── __init__.py
├── service.py           # RankingService orchestrator
├── context.py           # ScoringContext dataclass
├── config.py            # Scoring configuration
├── base.py              # BaseScorer ABC
├── registry.py          # Scorer plugin registry
└── scorers/
    ├── __init__.py
    ├── interest.py      # InterestScorer (rule-based)
    ├── affinity.py      # SourceAffinityScorer (rule-based)
    ├── popularity.py    # PopularityScorer (rule-based)
    ├── recency.py       # RecencyScorer (rule-based)
    ├── semantic.py      # SemanticScorer (embeddings)
    ├── relevance.py     # RelevanceScorer (LLM)
    └── quality.py       # QualityScorer (LLM)
```

## Unified LLM Architecture

All LLM operations (summarization, scoring, embeddings) share a single infrastructure to maximize efficiency.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      LLMService (unified)                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ContentProc. │  │  Scorers    │  │ Embeddings  │             │
│  │(summarize)  │  │ (rank)      │  │ (semantic)  │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                │                │                     │
│         └────────────────┼────────────────┘                     │
│                          ▼                                      │
│              ┌───────────────────────┐                          │
│              │   Request Batcher     │                          │
│              │  (groups operations)  │                          │
│              └───────────┬───────────┘                          │
│                          ▼                                      │
│              ┌───────────────────────┐                          │
│              │    Redis Cache        │                          │
│              │  (check before call)  │                          │
│              └───────────┬───────────┘                          │
│                          ▼                                      │
│              ┌───────────────────────┐                          │
│              │   LLM Provider        │                          │
│              │  (OpenAI/Anthropic)   │                          │
│              └───────────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

### LLMService Interface

```python
class LLMService:
    """Unified service for all LLM operations."""

    def __init__(
        self,
        provider: LLMProvider,
        cache: LLMCache,
        config: LLMConfig,
    ):
        self.provider = provider
        self.cache = cache
        self.config = config
        self.batcher = RequestBatcher(config.batch_size)

    # Content processing (replaces DataExtractor)
    def process_items(
        self, items: list[ContentItem]
    ) -> list[ProcessedContent]:
        """Batch process items: summarize + extract topics + quality score."""
        ...

    # Embeddings
    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings for texts (cached)."""
        ...

    # Scoring
    def score_relevance(
        self, items: list[UserFeedItemIn], context: ScoringContext
    ) -> list[float]:
        """Score items for user relevance."""
        ...
```

### Two-Phase Processing

LLM operations are split into user-independent and user-specific phases:

```
Phase 1: Feed Fetch (async, user-independent)
┌────────────────────────────────────────────────┐
│  1. Fetch items from sources                   │
│  2. Batch process with LLM:                    │
│     - Summarize content                        │
│     - Extract topic keywords                   │
│     - Score content quality                    │
│  3. Cache results by content_hash              │
└────────────────────────────────────────────────┘
                      │
                      ▼
Phase 2: Feed Generation (fast, user-specific)
┌────────────────────────────────────────────────┐
│  1. Load cached summaries/quality scores       │
│  2. Compute user-specific scores:              │
│     - Interest match (rule-based, fast)        │
│     - Source affinity (rule-based, fast)       │
│     - Semantic similarity (cached embeddings)  │
│     - LLM relevance (if enabled)               │
│  3. Combine scores and rank                    │
└────────────────────────────────────────────────┘
```

### Combined Prompts

Instead of separate LLM calls, combine operations:

```python
# BEFORE: 3 separate calls per item
summary = llm.summarize(item)           # Call 1
quality = llm.score_quality(item)       # Call 2
topics = llm.extract_topics(item)       # Call 3

# AFTER: 1 combined call for batch
results = llm.process_items(items[:20])  # 1 API call
# Each result: {summary, quality_score, topics}
```

**Combined Prompt Template:**

```python
PROCESS_ITEMS_PROMPT = '''
Analyze these articles:

{items_formatted}

For each item return:
- summary: 2-3 sentence summary (max 100 words)
- topics: 3-5 keyword topics for categorization
- quality: score 0.0-1.0 based on:
  - Informativeness (substance vs fluff)
  - Clarity (well-written vs confusing)
  - Not clickbait (honest title vs misleading)

Return JSON: {"results": [{"summary": "...", "topics": ["...", ...], "quality": 0.8}, ...]}
'''
```

### Caching Strategy

```python
# Cache keys and TTLs
CACHE_CONFIG = {
    # Content-based (user-independent) - long TTL
    "summary": {
        "key": "llm:summary:{content_hash}",
        "ttl": 86400 * 7,  # 7 days
    },
    "quality": {
        "key": "llm:quality:{content_hash}",
        "ttl": 86400 * 7,  # 7 days
    },
    "topics": {
        "key": "llm:topics:{content_hash}",
        "ttl": 86400 * 7,  # 7 days
    },
    "embedding": {
        "key": "llm:emb:{content_hash}",
        "ttl": 86400 * 30,  # 30 days
    },
    # User-specific - shorter TTL
    "relevance": {
        "key": "llm:rel:{user_id}:{content_hash}",
        "ttl": 3600,  # 1 hour
    },
}
```

**Content Hash Computation:**

```python
def content_hash(item: FeedItemIn) -> str:
    """Stable hash for cache keys."""
    content = f"{item.title}|{item.article_url or ''}|{item.source_name}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]
```

### Request Batching

```python
class RequestBatcher:
    """Batches LLM requests for efficiency."""

    def __init__(self, batch_size: int = 20, max_tokens: int = 4000):
        self.batch_size = batch_size
        self.max_tokens = max_tokens

    def create_batches(self, items: list[ContentItem]) -> list[list[ContentItem]]:
        """Split items into batches respecting size and token limits."""
        batches = []
        current_batch = []
        current_tokens = 0

        for item in items:
            item_tokens = self._estimate_tokens(item)
            if len(current_batch) >= self.batch_size or current_tokens + item_tokens > self.max_tokens:
                if current_batch:
                    batches.append(current_batch)
                current_batch = [item]
                current_tokens = item_tokens
            else:
                current_batch.append(item)
                current_tokens += item_tokens

        if current_batch:
            batches.append(current_batch)

        return batches
```

### LLM Provider Abstraction

```python
class LLMProvider(ABC):
    """Abstract base for LLM providers."""

    @abstractmethod
    def complete(
        self,
        prompt: str,
        system: str | None = None,
        response_format: str = "json",
        max_tokens: int = 1000,
    ) -> dict:
        """Send completion request."""
        pass

    @abstractmethod
    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings for texts."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI implementation."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.embedding_model = "text-embedding-3-small"

    def complete(self, prompt, system=None, response_format="json", max_tokens=1000):
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            response_format={"type": "json_object"} if response_format == "json" else None,
        )
        return json.loads(response.choices[0].message.content)

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]
```

### Graceful Degradation

```python
class LLMService:
    def process_items(self, items: list[ContentItem]) -> list[ProcessedContent]:
        results = []
        for batch in self.batcher.create_batches(items):
            try:
                batch_results = self._process_batch(batch)
                results.extend(batch_results)
            except (RateLimitError, TimeoutError, APIError) as e:
                logger.warning(f"LLM batch failed: {e}, using fallbacks")
                # Fallback: return items without LLM enrichment
                results.extend([
                    ProcessedContent(
                        summary=None,
                        topics=[],
                        quality_score=0.5,  # Neutral
                    )
                    for _ in batch
                ])
        return results
```

### File Structure

```
src/service/llm/
├── __init__.py          # Exports LLMService
├── service.py           # LLMService main class
├── provider.py          # LLMProvider ABC + OpenAIProvider
├── cache.py             # LLMCache (Redis wrapper)
├── batcher.py           # RequestBatcher
├── prompts.py           # Prompt templates
└── config.py            # LLMConfig dataclass

src/service/
├── content_processor.py # Uses LLMService for summarization
│                        # Replaces DataExtractor
└── ranking/
    └── scorers/
        ├── semantic.py  # Uses LLMService.get_embeddings()
        ├── relevance.py # Uses LLMService.score_relevance()
        └── quality.py   # Uses cached quality scores from content processing
```

### Cost Efficiency

| Metric | Before (DataExtractor) | After (LLMService) |
|--------|------------------------|---------------------|
| API calls per 100 items | 100 | 5-10 (batched) |
| Tokens per item | ~500 | ~250 (combined) |
| Cache hit rate | 0% | 70-90% |
| Latency per item | 1-2s | 50ms (cached) |
| Monthly cost (1000 items/day) | ~$15 | ~$2-3 |

## Future Enhancements

- **Recency decay**: Implement exponential time-based decay
- **Keyword extraction**: Use NLP to extract topics from content
- **Collaborative filtering**: Learn from similar users' preferences
- **A/B testing**: Compare ranking strategies with metrics
- **Per-source weights**: Allow users to boost/mute specific sources
- **Feedback learning**: Track click-through rates to improve scoring
- **Multi-model ensemble**: Combine multiple LLM providers for robustness
