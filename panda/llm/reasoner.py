"""Reasoner component to interpret plans and context into prompts/actions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseReasoner(ABC):
    """Reasoner contract."""

    @abstractmethod
    def select_action(self, plan_step: str, context: Dict[str, Any] | None = None) -> str:
        raise NotImplementedError


class Reasoner(BaseReasoner):
    """Simple rule-based placeholder."""

    def select_action(self, plan_step: str, context: Dict[str, Any] | None = None) -> str:
        # TODO: Replace with richer reasoning (tools, retrieval, reflection).
        context_note = f" with context {context}" if context else ""
        return f"Execute: {plan_step}{context_note}"


__all__ = ["BaseReasoner", "Reasoner"]

