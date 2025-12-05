"""LLM orchestrator wiring planner, reasoner, memory, security, and engine."""

from __future__ import annotations

from typing import Any, Dict, Optional
import uuid
from datetime import datetime

from .communication import BaseCommunicationManager, CommunicationManager
from .core import LLMEngine
from .memory import BaseMemory, ContextMemory
from .planner import BasePlanner, Planner, Plan
from .reasoner import BaseReasoner, Reasoner
from .security import BaseSecurityLayer, SecurityLayer


class LLMOrchestrator:
    """Coordinates the PANDA LLM workflow end-to-end.
    
    This orchestrator integrates all LLM components following the PANDA architecture:
    - Security layer for encryption/decryption
    - Communication manager for I/O normalization
    - Planner for task decomposition
    - Reasoner for action selection
    - LLM Engine for actual LLM calls
    - Context Memory for conversation history
    """

    def __init__(
        self,
        planner: Optional[BasePlanner] = None,
        reasoner: Optional[BaseReasoner] = None,
        engine: Optional[LLMEngine] = None,
        memory: Optional[BaseMemory] = None,
        security: Optional[BaseSecurityLayer] = None,
        comms: Optional[BaseCommunicationManager] = None,
    ) -> None:
        """Initialize the LLM orchestrator with all components.
        
        Args:
            planner: Planner instance (defaults to Planner)
            reasoner: Reasoner instance (defaults to Reasoner)
            engine: LLM Engine instance (defaults to LLMEngine)
            memory: Memory instance (defaults to ContextMemory)
            security: Security layer instance (defaults to SecurityLayer)
            comms: Communication manager instance (defaults to CommunicationManager)
        """
        self.planner = planner or Planner()
        self.reasoner = reasoner or Reasoner()
        self.engine = engine or LLMEngine()
        self.memory = memory or ContextMemory()
        self.security = security or SecurityLayer()
        self.comms = comms or CommunicationManager()

    def handle_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Top-level handler: normalize, decrypt, plan, reason, call LLM, store, format.
        
        This method follows the PANDA workflow:
        1. Normalize and decrypt input
        2. Create execution plan
        3. Reason about actions
        4. Execute LLM calls
        5. Store context in memory
        6. Encrypt and format output
        
        Args:
            payload: Input payload containing user request (may be encrypted)
            
        Returns:
            Dictionary with encrypted output and raw response
        """
        # Step 1: Normalize input and decrypt if needed
        normalized = self.comms.normalize_input(payload)
        encrypted_input = normalized.get("encrypted_input")
        if encrypted_input:
            user_input = self.security.decrypt(encrypted_input)
        else:
            user_input = normalized.get("input", "")
        
        # Sanitize input
        user_input = self.security.sanitize(user_input)

        # Step 2: Create execution plan
        constraints = normalized.get("constraints")
        plan = self.planner.create_plan(user_input, constraints=constraints)

        # Step 3: Get context from memory
        context = self.memory.get_context(limit=10)
        
        # Step 4: Reason about actions and execute plan steps
        # For now, execute first step as placeholder
        if plan.steps:
            first_step = plan.steps[0]
            action_prompt = self.reasoner.select_action(
                first_step.description, 
                context={"goal": plan.goal, "history": context, "step": first_step.model_dump()}
            )
            llm_response = self.engine.run(action_prompt)
        else:
            llm_response = {"response": "No plan steps generated"}

        # Step 5: Store in memory
        self.memory.add(role="user", content=user_input)
        self.memory.add(role="assistant", content=str(llm_response.get("response", llm_response)))

        # Step 6: Encrypt output and format response
        response_text = str(llm_response.get("response", llm_response))
        encrypted_output = self.security.encrypt(response_text)
        
        return self.comms.format_output({
            "encrypted_output": encrypted_output,
            "raw": llm_response,
            "plan": plan.model_dump() if isinstance(plan, Plan) else plan
        })

    def create_execution_plan(self, objective: str, constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create an execution plan compatible with router/models.py ExecutionPlanResponse.
        
        Args:
            objective: User's high-level objective
            constraints: Optional constraints (time, budget, preferences)
            
        Returns:
            Dictionary compatible with ExecutionPlanResponse structure
        """
        plan = self.planner.create_plan(objective, constraints=constraints)
        plan_id = str(uuid.uuid4())
        
        # Calculate total estimated time
        total_time = "N/A"
        if plan.steps:
            # Simple heuristic - sum up durations (placeholder)
            total_time = f"{len(plan.steps) * 10} minutes"
        
        return {
            "plan_id": plan_id,
            "goal": plan.goal,
            "tasks": [step.model_dump() for step in plan.steps],
            "total_estimated_time": total_time
        }


__all__ = ["LLMOrchestrator"]

