import os

# Feature flags
ENABLE_SUMMARIZATION = os.environ.get("ENABLE_SUMMARIZATION", "").lower() == "true"
CREATE_ITEMS_ON_STARTUP = os.environ.get("CREATE_ITEMS_ON_STARTUP", "").lower() == "true"

# API keys
OPEN_AI_KEY = os.environ.get("OPENAI_API_KEY", "")
HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY", "")

# Redis
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# LLM settings
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
LLM_EMBEDDING_MODEL = os.environ.get("LLM_EMBEDDING_MODEL", "text-embedding-3-small")
LLM_BATCH_SIZE = int(os.environ.get("LLM_BATCH_SIZE", "10"))
LLM_CACHE_TTL = int(os.environ.get("LLM_CACHE_TTL", "604800"))  # 7 days
