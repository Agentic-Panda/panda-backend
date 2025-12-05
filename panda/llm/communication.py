"""Communication layer to interface with UI/API and external systems."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseCommunicationManager(ABC):
    """Communication contract."""

    @abstractmethod
    def normalize_input(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def format_output(self, result: Any) -> Dict[str, Any]:
        raise NotImplementedError


class CommunicationManager(BaseCommunicationManager):
    """Validates and normalizes inbound/outbound messages."""

    def normalize_input(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: Add schema validation and role-based access checks.
        return payload

    def format_output(self, result: Any) -> Dict[str, Any]:
        return {"result": result}


__all__ = ["BaseCommunicationManager", "CommunicationManager"]

