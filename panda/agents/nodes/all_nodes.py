from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from panda.core.llm.factory import LLMFactory, LLMProvider
from panda.core.llm.prompts import (
    MASTER_SUPERVISOR_PROMPT,
    EMAIL_AGENT_PROMPT,
    SCHEDULER_AGENT_PROMPT,
    BOOKING_AGENT_PROMPT,
    CHITCHAT_AGENT_PROMPT,
    HEALTH_MONITOR_PROMPT
)
from panda.models.agents.state import MasterState
from panda.models.agents.response import (
    SupervisorRouterResponse,
    EmailAgentResponse,
    SchedulerAgentResponse,
    BookingAgentResponse,
    ChitChatResponse,
    HealthMonitorResponse
)

from panda.core.tools.calendar import CalendarTools


# ============================================================================
# SUPERVISOR NODE
# ============================================================================

supervisor_llm = LLMFactory.create_client(
    provider=LLMProvider.OPENROUTER,
    model_name="mistralai/devstral-2512:free",
).with_structured_output(SupervisorRouterResponse)

supervisor_prompt = ChatPromptTemplate.from_messages([
    ("system", MASTER_SUPERVISOR_PROMPT),
    MessagesPlaceholder(variable_name="messages"),
])

async def supervisor_node(state: MasterState):
    """Main routing supervisor"""
    chain = supervisor_prompt | supervisor_llm
    
    decision = await chain.ainvoke({
        "messages": state["messages"]
    })
    
    # Update tracking
    return {
        "next_agent": decision.next_agent,
        "current_agent": "supervisor",
        "context": {
            **state.get("context", {}),
        }
    }


# ============================================================================
# EMAIL AGENT NODE
# ============================================================================

email_llm = LLMFactory.create_client(
    provider=LLMProvider.OPENROUTER,
    model_name="mistralai/devstral-2512:free",
).with_structured_output(EmailAgentResponse)

email_prompt = ChatPromptTemplate.from_messages([
    ("system", EMAIL_AGENT_PROMPT),
    ("system", "Current context: {context}"),
    MessagesPlaceholder(variable_name="messages"),
])

async def email_agent_node(state: MasterState):
    """Handles all email-related tasks"""
    
    # Check if coming from polling or user request
    context = state.get("context", {})
    email_data = state.get("email_data", {})
    
    # Build context for LLM
    email_context = f"""
    User ID: {state.get('user_id')}
    Pending Actions: {state.get('pending_actions', [])}
    Email Data: {email_data}
    """
    
    chain = email_prompt | email_llm
    
    response = await chain.ainvoke({
        "context": email_context,
        "messages": state["messages"]
    })
    
    # Perform actions based on response
    new_pending_actions = []
    email_updates = {}
    
    if response.action == "reply" and response.draft_reply:
        # Store drafted reply
        email_updates["drafted_replies"] = [
            *email_data.get("drafted_replies", []),
            response.draft_reply
        ]
    
    elif response.action == "send_new":
        # TODO: Implement email sending via EmailTools
        email_to_send = {
            "to": context.get("recipient"),
            "subject": context.get("subject"),
            "body": response.draft_reply,
            "timestamp": datetime.now()
        }
        # await EmailTools.send_email(email_to_send)
        email_updates["emails_sent"] = True
    
    # Check if scheduling is needed
    if response.requires_scheduling and response.calendar_event:
        new_pending_actions.append({
            "type": "schedule",
            "data": response.calendar_event,
            "source": "email"
        })
    
    # Extract important info to database
    if response.is_important:
        # TODO: Store in database
        # await EmailTools.store_email_metadata(response.key_details)
        pass
    
    # Update state
    next_agent = response.next_agent
    if response.requires_scheduling:
        next_agent = "scheduler_agent"
    
    return {
        "next_agent": next_agent,
        "current_agent": "email_agent",
        "email_data": {**email_data, **email_updates},
        "pending_actions": new_pending_actions,
        "messages": [AIMessage(content=f"Email processed. Action: {response.action}. {response.draft_reply or ''}")],
        "context": {
            **context,
            "last_email_action": response.action,
            "email_priority": response.priority
        }
    }


# ============================================================================
# SCHEDULER AGENT NODE
# ============================================================================

scheduler_llm = LLMFactory.create_client(
    provider=LLMProvider.OPENROUTER,
    model_name="mistralai/devstral-2512:free",
).with_structured_output(SchedulerAgentResponse)

scheduler_prompt = ChatPromptTemplate.from_messages([
    ("system", SCHEDULER_AGENT_PROMPT),
    ("system", "Current calendar context: {context}"),
    MessagesPlaceholder(variable_name="messages"),
])

async def scheduler_agent_node(state: MasterState):
    """Handles calendar and task management"""
    
    context = state.get("context", {})
    scheduler_data = state.get("scheduler_data", {})
    pending_actions = state.get("pending_actions", [])
    
    # Check for pending scheduling actions from email
    schedule_requests = [
        action for action in pending_actions 
        if action.get("type") == "schedule"
    ]
    
    # Build context
    calendar_context = f"""
    User ID: {state.get('user_id')}
    Pending Schedule Requests: {schedule_requests}
    Current Events: {scheduler_data.get('calendar_events', [])}
    Conflicts: {scheduler_data.get('conflicts', [])}
    """
    
    chain = scheduler_prompt | scheduler_llm
    
    response = await chain.ainvoke({
        "context": calendar_context,
        "messages": state["messages"]
    })
    
    # Perform calendar operations
    scheduler_updates = {}
    response_message = ""
    
    if response.action == "create_event" and response.event_details:
        # Check for conflicts first
        conflicts = await CalendarTools.check_conflicts(response.event_details)
        
        if conflicts:
            response_message = f"⚠️ Scheduling conflict detected: {conflicts}. "
            response_message += f"Suggestions: {response.suggestions}"
            scheduler_updates["conflicts"] = conflicts
        else:
            # TODO: Create event in calendar
            # event_id = await CalendarTools.create_event(response.event_details)
            response_message = f"✓ Event created: {response.event_details.get('title')}"
            scheduler_updates["calendar_events"] = [
                *scheduler_data.get("calendar_events", []),
                response.event_details
            ]
    
    elif response.action == "create_todo":
        # TODO: Add to todo list
        # await CalendarTools.create_todo(response.event_details)
        response_message = f"✓ Todo added: {response.event_details.get('task')}"
    
    elif response.action == "set_reminder":
        # TODO: Set reminder
        # await CalendarTools.set_reminder(response.event_details)
        response_message = f"✓ Reminder set for: {response.event_details.get('time')}"
    
    elif response.action == "list_events":
        # TODO: Fetch events
        # events = await CalendarTools.get_events(date_range)
        events = scheduler_data.get("calendar_events", [])
        response_message = f"Your upcoming events: {events}"
    
    # Clear processed pending actions
    remaining_actions = [
        action for action in pending_actions 
        if action.get("type") != "schedule"
    ]
    
    next_agent = response.next_agent
    if response.requires_human_decision:
        next_agent = "human_review"
    
    return {
        "next_agent": next_agent,
        "current_agent": "scheduler_agent",
        "scheduler_data": {**scheduler_data, **scheduler_updates},
        "pending_actions": remaining_actions,
        "messages": [AIMessage(content=response_message)],
        "context": {
            **context,
            "last_schedule_action": response.action,
            "conflicts_found": response.conflicts_found
        },
        "requires_human": response.requires_human_decision
    }


# ============================================================================
# BOOKING AGENT NODE
# ============================================================================

booking_llm = LLMFactory.create_client(
    provider=LLMProvider.OPENROUTER,
    model_name="mistralai/devstral-2512:free",  # Use better model for complex booking
).with_structured_output(BookingAgentResponse)

booking_prompt = ChatPromptTemplate.from_messages([
    ("system", BOOKING_AGENT_PROMPT),
    ("system", "Booking context: {context}"),
    MessagesPlaceholder(variable_name="messages"),
])

async def booking_agent_node(state: MasterState):
    """Handles booking requests"""
    
    context = state.get("context", {})
    booking_data = state.get("booking_data", {})
    
    booking_context = f"""
    User ID: {state.get('user_id')}
    Current Booking: {booking_data}
    User Preferences: {context.get('user_preferences', {})}
    """
    
    chain = booking_prompt | booking_llm
    
    response = await chain.ainvoke({
        "context": booking_context,
        "messages": state["messages"]
    })
    
    booking_updates = {
        "booking_type": response.booking_type
    }
    response_message = ""
    
    if response.requires_more_info:
        # Ask user for missing information
        missing = ", ".join(response.missing_params)
        response_message = f"I need more information to proceed: {missing}"
        next_agent = "human_review"
    
    elif response.search_performed and response.options_found > 0:
        # Present options to user
        response_message = f"I found {response.options_found} options for your {response.booking_type}:\n\n"
        
        for i, option in enumerate(response.top_recommendations, 1):
            response_message += f"{i}. {option}\n"
        
        response_message += "\n⚠️ Please review and confirm your selection."
        
        booking_updates["search_results"] = response.top_recommendations
        booking_updates["ready_for_booking"] = response.ready_for_booking
        next_agent = "human_review"
    
    else:
        # Start search process
        # TODO: Implement booking search
        # results = await BookingTools.search(
        #     booking_type=response.booking_type,
        #     params=context
        # )
        response_message = f"Searching for {response.booking_type} options..."
        next_agent = "booking_agent"  # Loop back after search
    
    return {
        "next_agent": next_agent,
        "current_agent": "booking_agent",
        "booking_data": {**booking_data, **booking_updates},
        "messages": [AIMessage(content=response_message)],
        "requires_human": True,  # Always require human for bookings
        "context": {
            **context,
            "booking_type": response.booking_type
        }
    }


# ============================================================================
# CHITCHAT AGENT NODE
# ============================================================================

chitchat_llm = LLMFactory.create_client(
    provider=LLMProvider.OPENROUTER,
    model_name="mistralai/devstral-2512:free",  # Use lite model for cost savings
).with_structured_output(ChitChatResponse)

chitchat_prompt = ChatPromptTemplate.from_messages([
    ("system", CHITCHAT_AGENT_PROMPT),
    MessagesPlaceholder(variable_name="messages"),
])

async def chitchat_agent_node(state: MasterState):
    """Handles casual conversation"""
    
    chain = chitchat_prompt | chitchat_llm
    
    response = await chain.ainvoke({
        "messages": state["messages"]
    })
    
    next_agent = response.next_agent
    
    # Check for escalation
    if response.requires_escalation and response.escalate_to:
        next_agent = response.escalate_to
    
    return {
        "next_agent": next_agent,
        "current_agent": "chitchat_agent",
        "messages": [AIMessage(content=response.response_text)],
        "context": {
            **state.get("context", {}),
            "detected_intent": response.detected_intent,
            "escalated": response.requires_escalation
        }
    }


# ============================================================================
# HEALTH MONITOR NODE
# ============================================================================

health_llm = LLMFactory.create_client(
    provider=LLMProvider.OPENROUTER,
    model_name="mistralai/devstral-2512:free",
).with_structured_output(HealthMonitorResponse)

health_prompt = ChatPromptTemplate.from_messages([
    ("system", HEALTH_MONITOR_PROMPT),
    ("system", "Interaction history: {history}"),
    MessagesPlaceholder(variable_name="messages"),
])

async def health_monitor_node(state: MasterState):
    """Monitors user emotional and mental wellbeing"""
    
    interaction_history = state.get("interaction_history", [])
    
    # Build history summary
    history_summary = "\n".join([
        f"[{h.get('timestamp')}] {h.get('agent')}: {h.get('message')}"
        for h in interaction_history[-10:]  # Last 10 interactions
    ])
    
    chain = health_prompt | health_llm
    
    response = await chain.ainvoke({
        "history": history_summary,
        "messages": state["messages"]
    })
    
    # Update emotion state
    emotion_state = {
        "sentiment_score": response.sentiment_score,
        "emotion": response.emotion_detected,
        "stress_level": response.stress_level,
        "alert_level": response.alert_level,
        "timestamp": datetime.now(),
        "recommendations": response.recommendations
    }
    
    # Create optional message if alert level is high
    health_message = None
    if response.alert_level in ["concern", "alert"] and response.should_suggest_break:
        health_message = AIMessage(
            content=f"💙 {response.recommendations[0] if response.recommendations else 'Consider taking a break.'}"
        )
    
    return {
        "current_agent": "health_monitor",
        "emotion_state": emotion_state,
        "stress_level": response.stress_level,
        "messages": [health_message] if health_message else [],
        "context": {
            **state.get("context", {}),
            "health_alert": response.alert_level,
            "sentiment_trend": response.trending_sentiment
        }
    }


# ============================================================================
# HUMAN IN THE LOOP NODE
# ============================================================================

async def human_review_node(state: MasterState):
    """Handles human approval and feedback"""
    
    context = state.get("context", {})
    
    # This node typically waits for user input
    # In practice, this would pause the graph and wait for user action
    
    return {
        "current_agent": "human_review",
        "next_agent": "supervisor",  # Return to supervisor after human input
        "messages": [
            SystemMessage(content="⏸️ Waiting for your confirmation...")
        ]
    }