import asyncio

from fastapi import APIRouter

from ..core.llm.factory import LLMProvider, LLMFactory

from datetime import datetime
from langchain_core.messages import HumanMessage

from panda.agents.graph import create_agent_graph, create_polling_graph
from panda.models.agents.state import MasterState

#from panda.agents.graph import build_and_run_graph

router = APIRouter()


class PersonalAssistant:
    """Main personal assistant orchestrator"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.graph = create_agent_graph()
        self.polling_graph = create_polling_graph()
        self.polling_task = None
    
    async def chat(self, message: str, conversation_id: str = None) -> dict:
        """
        Main chat interface
        
        Args:
            message: User's message
            conversation_id: Optional conversation ID for context
        
        Returns:
            Response dict with agent outputs
        """
        
        # Initialize state
        initial_state: MasterState = {
            "messages": [HumanMessage(content=message)],
            "current_agent": "supervisor",
            "next_step": "",
            "user_id": self.user_id,
            "conversation_id": conversation_id or f"conv_{datetime.now().timestamp()}",
            "context": {},
            "pending_actions": [],
            "requires_human": False,
            "human_feedback": None,
            "interaction_history": [],
            "emotion_state": {},
            "stress_level": 0.0,
            "email_data": {},
            "scheduler_data": {},
            "booking_data": {},
            "timestamp": datetime.now(),
            "session_metadata": {}
        }
        
        # Run the graph
        result = await self.graph.ainvoke(initial_state)
        
        # Extract response
        return self._format_response(result)
    
    def _format_response(self, state: dict) -> dict:
        """Format the final state into a user-friendly response"""
        
        messages = state.get("messages", [])
        ai_messages = [m.content for m in messages if hasattr(m, 'content') and m.content]
        
        response = {
            "response": "\n".join(ai_messages[-3:]),  # Last 3 messages
            "agent": state.get("current_agent"),
            "requires_action": state.get("requires_human", False),
            "emotion_state": state.get("emotion_state", {}),
            "pending_actions": state.get("pending_actions", [])
        }
        
        return response
    
    async def start_polling(self, interval_seconds: int = 300):
        """
        Start automated email polling
        
        Args:
            interval_seconds: Polling interval (default: 5 minutes)
        """
        
        async def poll_loop():
            while True:
                try:
                    print(f"[{datetime.now()}] Polling for new emails...")
                    
                    poll_state: MasterState = {
                        "messages": [],
                        "current_agent": "poll_emails",
                        "next_step": "",
                        "user_id": self.user_id,
                        "conversation_id": f"poll_{datetime.now().timestamp()}",
                        "context": {"automated": True},
                        "pending_actions": [],
                        "requires_human": False,
                        "human_feedback": None,
                        "interaction_history": [],
                        "emotion_state": {},
                        "stress_level": 0.0,
                        "email_data": {},
                        "scheduler_data": {},
                        "booking_data": {},
                        "timestamp": datetime.now(),
                        "session_metadata": {}
                    }
                    
                    result = await self.polling_graph.ainvoke(poll_state)
                    
                    # Log results
                    emails_processed = len(result.get("email_data", {}).get("processed_email_ids", []))
                    if emails_processed > 0:
                        print(f"✓ Processed {emails_processed} new emails")
                    
                except Exception as e:
                    print(f"❌ Polling error: {e}")
                
                # Wait for next poll
                await asyncio.sleep(interval_seconds)
        
        # Start polling in background
        self.polling_task = asyncio.create_task(poll_loop())
        print(f"📧 Email polling started (interval: {interval_seconds}s)")
    
    async def stop_polling(self):
        """Stop automated polling"""
        if self.polling_task:
            self.polling_task.cancel()
            print("📧 Email polling stopped")
    
    async def provide_feedback(self, conversation_id: str, feedback: str):
        """
        Provide human feedback for pending actions
        
        Use this when requires_action=True in response
        """
        # This would continue the graph execution with human input
        # Implementation depends on your state persistence strategy
        pass






# TODO change response model
@router.get("/testmodelflash")
async def test_flash():
    #await build_and_run_graph()

    return {"response": 'hi'}


@router.get("/test")
async def test_model():
    assistant = PersonalAssistant(user_id="user_123")
    
    # Example 1: Casual chat
    print("\n" + "="*60)
    print("Example 1: Casual Chat")
    print("="*60)
    response = await assistant.chat("Hey, how are you doing today?")
    print(f"Response: {response['response']}")
    print(f"Agent: {response['agent']}")
    
    # Example 2: Email query
    print("\n" + "="*60)
    print("Example 2: Email Query")
    print("="*60)
    response = await assistant.chat("Check my emails and let me know if there's anything important")
    print(f"Response: {response['response']}")
    print(f"Pending Actions: {response['pending_actions']}")
    
    # Example 3: Schedule meeting
    print("\n" + "="*60)
    print("Example 3: Schedule Meeting")
    print("="*60)
    response = await assistant.chat("Schedule a meeting with the team for tomorrow at 2pm")
    print(f"Response: {response['response']}")
    print(f"Requires Action: {response['requires_action']}")
    
    # Example 4: Booking request
    #print("\n" + "="*60)
    #print("Example 4: Booking Request")
    #print("="*60)
    #response = await assistant.chat("I need to book a flight to San Francisco for next week")
    #print(f"Response: {response['response']}")
    #print(f"Requires Action: {response['requires_action']}")
    
    # Example 5: Complex multi-step
    print("\n" + "="*60)
    print("Example 5: Complex Request")
    print("="*60)
    response = await assistant.chat(
        "Check my emails for any meeting requests and add them to my calendar"
    )
    print(f"Response: {response['response']}")
    print(f"Pending Actions: {response['pending_actions']}")

    return {"response": 'hi'}