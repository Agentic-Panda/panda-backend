"""LLM integration stubs (Gemini placeholder)."""

from __future__ import annotations

from abc import ABC, abstractmethod
import os
from typing import Any, Dict, Optional


class BaseLLMClient(ABC):
    """Abstract LLM client interface."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """Return a completion for the prompt."""
        raise NotImplementedError


class GeminiClient(BaseLLMClient):
    """Lightweight wrapper for a Gemini-style LLM API."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-pro") -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY or pass api_key.")

    def generate(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """Generate a completion for the given prompt.

        This is a placeholder; replace with real HTTP call to Gemini endpoint.
        """
        # TODO: Implement API request to Gemini service and handle errors.
        return {
            "model": self.model,
            "prompt": prompt,
            "kwargs": kwargs,
            "response": "This is a stub response from GeminiClient.",
        }


class LLMEngine:
    """Thin engine abstraction to swap LLM providers without changing orchestration."""

    def __init__(self, client: Optional[BaseLLMClient] = None) -> None:
        self.client = client or GeminiClient()

    def run(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        return self.client.generate(prompt, **kwargs)


__all__ = ["BaseLLMClient", "GeminiClient", "LLMEngine"]

