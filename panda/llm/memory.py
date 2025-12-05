"""Context memory stub for PANDA."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseMemory(ABC):
    """Memory contract for context storage."""

    @abstractmethod
    def add(self, role: str, content: str, metadata: Dict[str, Any] | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        raise NotImplementedError


class ContextMemory(BaseMemory):
    """In-memory store; swap with DB or vector store later."""

    def __init__(self) -> None:
        self._history: List[Dict[str, Any]] = []

    def add(self, role: str, content: str, metadata: Dict[str, Any] | None = None) -> None:
        self._history.append({"role": role, "content": content, "metadata": metadata or {}})

    def recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._history[-limit:]

    def clear(self) -> None:
        self._history.clear()


__all__ = ["BaseMemory", "ContextMemory"]

