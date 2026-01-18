import os

ENABLE_SUMMARIZATION = os.environ.get("ENABLE_SUMMARIZATION", "").lower() == "true"

CREATE_ITEMS_ON_STARTUP = os.environ.get("CREATE_ITEMS_ON_STARTUP", "").lower() == "true"

OPEN_AI_KEY = os.environ.get("OPENAI_API_KEY", "")
HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY", "")
