"""LLM orchestrator wiring planner, reasoner, memory, security, and engine."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .communication import BaseCommunicationManager, CommunicationManager
from .core import LLMEngine
from .memory import BaseMemory, ContextMemory
from .planner import BasePlanner, Planner
from .reasoner import BaseReasoner, Reasoner
from .security import BaseSecurityLayer, SecurityLayer


class LLMOrchestrator:
    """Coordinates the PANDA LLM workflow end-to-end."""

    def __init__(
        self,
        planner: Optional[BasePlanner] = None,
        reasoner: Optional[BaseReasoner] = None,
        engine: Optional[LLMEngine] = None,
        memory: Optional[BaseMemory] = None,
        security: Optional[BaseSecurityLayer] = None,
        comms: Optional[BaseCommunicationManager] = None,
    ) -> None:
        self.planner = planner or Planner()
        self.reasoner = reasoner or Reasoner()
        self.engine = engine or LLMEngine()
        self.memory = memory or ContextMemory()
        self.security = security or SecurityLayer()
        self.comms = comms or CommunicationManager()

    def handle_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Top-level handler: normalize, decrypt, plan, reason, call LLM, store, format."""
        normalized = self.comms.normalize_input(payload)
        encrypted_input = normalized.get("encrypted_input")
        if encrypted_input:
            user_input = self.security.decrypt(encrypted_input)
        else:
            user_input = normalized.get("input", "")

        plan = self.planner.create_plan(user_input)

        # For now, run first step only as placeholder.
        first_step = plan.steps[0].description if plan.steps else "No-op"
        action_prompt = self.reasoner.select_action(first_step, context={"goal": plan.goal})
        llm_response = self.engine.run(action_prompt)

        self.memory.add(role="user", content=user_input)
        self.memory.add(role="assistant", content=str(llm_response))

        encrypted_output = self.security.encrypt(str(llm_response))
        return self.comms.format_output({"encrypted_output": encrypted_output, "raw": llm_response})


__all__ = ["LLMOrchestrator"]

