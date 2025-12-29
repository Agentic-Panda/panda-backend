from langgraph.graph import StateGraph, END
from typing import Literal

from panda.models.agents.state import MasterState
from panda.agents.nodes.all_nodes import (
    supervisor_node,
    email_agent_node,
    scheduler_agent_node,
    booking_agent_node,
    chitchat_agent_node,
    health_monitor_node,
    human_review_node
)


# ============================================================================
# ROUTING FUNCTIONS
# ============================================================================

def route_supervisor(state: MasterState) -> str:
    """Route from supervisor to appropriate agent"""
    next_agent = state.get("next_agent", "chitchat_agent")
    
    # Check if human review is required
    if state.get("requires_human"):
        return "human_review"
    
    return next_agent


def route_email_agent(state: MasterState) -> str:
    """Route from email agent"""
    next_agent = state.get("next_agent", "supervisor")
    
    # Check pending actions for scheduling
    pending = state.get("pending_actions", [])
    has_schedule_action = any(a.get("type") == "schedule" for a in pending)
    
    if has_schedule_action:
        return "scheduler_agent"
    
    if state.get("requires_human"):
        return "human_review"
    
    # Always pass through health monitor for user interactions
    #if next_agent == "supervisor":
        #return "health_monitor"
    
    return next_agent


def route_scheduler_agent(state: MasterState) -> str:
    """Route from scheduler agent"""
    next_agent = state.get("next_agent", "supervisor")
    
    if state.get("requires_human"):
        return "human_review"
    
    # Always monitor user interactions
    #if next_agent == "supervisor":
        #return "health_monitor"
    
    return next_agent


def route_booking_agent(state: MasterState) -> str:
    """Route from booking agent - always needs human review"""
    # Bookings always require human confirmation
    return "human_review"


def route_chitchat_agent(state: MasterState) -> str:
    """Route from chitchat agent"""
    next_agent = state.get("next_agent", "END")
    
    # Check if escalation is needed
    if next_agent in ["email_agent", "scheduler_agent", "booking_agent"]:
        return next_agent
    
    #if next_agent == "supervisor":
        #return "health_monitor"
    
    # Monitor even casual conversations
    #if next_agent == "END":
        #return "health_monitor"
    
    return next_agent


def route_health_monitor(state: MasterState) -> str:
    """Route from health monitor - non-blocking"""
    # Health monitor always returns to supervisor or ends
    next_agent = state.get("next_agent")
    
    # If no explicit next step, check context
    if not next_agent:
        # If high alert, might want human review
        if state.get("emotion_state", {}).get("alert_level") == "alert":
            # Don't force, just pass through
            pass
        return "supervisor"
    
    if next_agent == "END":
        return END
    
    return "supervisor"


def route_human_review(state: MasterState) -> str:
    """Route from human review back to supervisor"""
    # After human input, usually return to supervisor
    human_feedback = state.get("human_feedback")
    
    if human_feedback:
        # Human provided input, go back to supervisor for routing
        return "supervisor"
    
    # Still waiting for human input
    return END


# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def create_agent_graph():
    """Create and compile the multi-agent graph"""
    
    # Initialize graph with state schema
    workflow = StateGraph(MasterState)
    
    # Add all agent nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("email_agent", email_agent_node)
    workflow.add_node("scheduler_agent", scheduler_agent_node)
    workflow.add_node("booking_agent", booking_agent_node)
    workflow.add_node("chitchat_agent", chitchat_agent_node)
    #workflow.add_node("health_monitor", health_monitor_node)
    workflow.add_node("human_review", human_review_node)
    
    # Set entry point
    workflow.set_entry_point("supervisor")
    
    # Add conditional edges from supervisor
    workflow.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {
            "email_agent": "email_agent",
            "scheduler_agent": "scheduler_agent",
            "booking_agent": "booking_agent",
            "chitchat_agent": "chitchat_agent",
            #"health_monitor": "health_monitor",
            "human_review": "human_review",
            "END": END
        }
    )
    
    # Email agent routing
    workflow.add_conditional_edges(
        "email_agent",
        route_email_agent,
        {
            "scheduler_agent": "scheduler_agent",
            "human_review": "human_review",
            #"health_monitor": "health_monitor",
            "supervisor": "supervisor",
            "END": END
        }
    )
    
    # Scheduler agent routing
    workflow.add_conditional_edges(
        "scheduler_agent",
        route_scheduler_agent,
        {
            "human_review": "human_review",
            #"health_monitor": "health_monitor",
            "supervisor": "supervisor",
            "END": END
        }
    )
    
    # Booking agent always goes to human review
    workflow.add_conditional_edges(
        "booking_agent",
        route_booking_agent,
        {
            "human_review": "human_review",
            "END": END
        }
    )
    
    # Chitchat agent routing
    workflow.add_conditional_edges(
        "chitchat_agent",
        route_chitchat_agent,
        {
            "email_agent": "email_agent",
            "scheduler_agent": "scheduler_agent",
            "booking_agent": "booking_agent",
            #"health_monitor": "health_monitor",
            "supervisor": "supervisor",
            "END": END
        }
    )
    
    # Health monitor routing
    #workflow.add_conditional_edges(
    #    "health_monitor",
    #    route_health_monitor,
    #    {
    #        "supervisor": "supervisor",
    #        "END": END
    #    }
    #)
    
    # Human review routing
    workflow.add_conditional_edges(
        "human_review",
        route_human_review,
        {
            "supervisor": "supervisor",
            "END": END
        }
    )
    
    # Compile the graph
    return workflow.compile()


# ============================================================================
# POLLING GRAPH (for automated email checking)
# ============================================================================

def create_polling_graph():
    """Create a separate graph for automated email polling"""
    
    poll_workflow = StateGraph(MasterState)
    
    # Simple polling flow
    async def poll_emails_node(state: MasterState):
        """Poll for new emails"""
        from panda.core.tools.email import EmailTools
        
        user_id = state.get("user_id")
        emails = await EmailTools.fetch_emails(user_id, unread_only=True)
        
        return {
            "email_data": {
                "unprocessed_emails": emails,
                "poll_timestamp": state.get("timestamp")
            },
            "messages": [],  # No user messages in polling
            "next_agent": "email_agent" if emails else "END"
        }
    
    poll_workflow.add_node("poll_emails", poll_emails_node)
    poll_workflow.add_node("email_agent", email_agent_node)
    poll_workflow.add_node("scheduler_agent", scheduler_agent_node)
    #poll_workflow.add_node("health_monitor", health_monitor_node)
    
    # Set entry point
    poll_workflow.set_entry_point("poll_emails")
    
    # Routing
    def route_poll_emails(state: MasterState) -> str:
        if state.get("next_agent") == "email_agent":
            return "email_agent"
        return END
    
    poll_workflow.add_conditional_edges(
        "poll_emails",
        route_poll_emails,
        {
            "email_agent": "email_agent",
            "END": END
        }
    )
    
    poll_workflow.add_conditional_edges(
        "email_agent",
        route_email_agent,
        {
            "scheduler_agent": "scheduler_agent",
            #"health_monitor": "health_monitor",
            "END": END
        }
    )
    
    poll_workflow.add_edge("scheduler_agent", END)
    #poll_workflow.add_edge("health_monitor", END)
    
    return poll_workflow.compile()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def visualize_graph(graph, output_path: str = "agent_graph.png"):
    """Generate visual representation of the graph"""
    try:
        from IPython.display import Image, display
        
        img = Image(graph.get_graph().draw_mermaid_png())
        
        # Save to file
        with open(output_path, "wb") as f:
            f.write(img.data)
        
        print(f"Graph visualization saved to {output_path}")
        return img
    
    except Exception as e:
        print(f"Could not generate graph visualization: {e}")
        return None