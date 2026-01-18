"""LLM provider abstraction."""

import json
from abc import ABC, abstractmethod

from openai import OpenAI

from utils.logger import get_logger

logger = get_logger(__name__)


class LLMProvider(ABC):
    """Abstract base for LLM providers."""

    @abstractmethod
    def complete(
        self,
        prompt: str,
        system: str | None = None,
        response_format: str = "json",
        max_tokens: int = 1000,
        temperature: float = 0.3,
    ) -> dict | str:
        """Send completion request.

        Args:
            prompt: User prompt
            system: Optional system message
            response_format: "json" or "text"
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            Parsed JSON dict if response_format="json", else raw string
        """
        pass

    @abstractmethod
    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings for texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI implementation."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        embedding_model: str = "text-embedding-3-small",
    ):
        if not api_key:
            logger.warning("OpenAI API key not provided, LLM features disabled")
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.model = model
        self.embedding_model = embedding_model

    def complete(
        self,
        prompt: str,
        system: str | None = None,
        response_format: str = "json",
        max_tokens: int = 1000,
        temperature: float = 0.3,
    ) -> dict | str:
        if not self.client:
            raise RuntimeError("OpenAI client not initialized (missing API key)")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            response_format={"type": "json_object"} if response_format == "json" else None,
        )

        content = response.choices[0].message.content
        if response_format == "json":
            return json.loads(content)
        return content

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        if not self.client:
            raise RuntimeError("OpenAI client not initialized (missing API key)")

        if not texts:
            return []

        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]
