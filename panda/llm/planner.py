"""Planner component for breaking tasks into structured plans."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class PlanStep:
    description: str
    depends_on: list[int] | None = None


@dataclass
class Plan:
    goal: str
    steps: List[PlanStep]


class BasePlanner(ABC):
    """Planner contract."""

    @abstractmethod
    def create_plan(self, goal: str) -> Plan:
        raise NotImplementedError


class Planner(BasePlanner):
    """Very light heuristic planner stub."""

    def create_plan(self, goal: str) -> Plan:
        # TODO: Replace with actual planning logic or LLM-assisted planning.
        steps = [
            PlanStep(description="Clarify goal and constraints"),
            PlanStep(description="Gather required data"),
            PlanStep(description="Propose solution or action"),
            PlanStep(description="Summarize and return result"),
        ]
        return Plan(goal=goal, steps=steps)


__all__ = ["BasePlanner", "Planner", "Plan", "PlanStep"]

