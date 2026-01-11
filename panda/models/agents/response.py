from typing import Literal, Optional
from pydantic import BaseModel, Field


class SupervisorRouterResponse(BaseModel):
    """Supervisor routing decision"""
    next_agent: Optional[Literal[
        "email_agent",
        "scheduler_agent", 
        "booking_agent",
        "chitchat_agent",
        "health_monitor",
        "human_review",
        "END"
    ]] = Field(default=None, description="The label / key of next agent to route to (label only)")
    #reasoning: str = Field(description="Why this routing decision was made")
    #urgency: Literal["low", "medium", "high"] = Field(default="medium")


class EmailAgentResponse(BaseModel):
    """Email agent analysis and actions"""
    action: Literal["reply", "schedule", "ignore", "forward", "send_new"] = Field(
        description="Action to take with this email"
    )
    is_spam: bool = Field(description="Whether email is spam")
    is_important: bool = Field(description="Whether email requires attention")
    priority: Literal["low", "medium", "high", "urgent"] = Field(default="medium")
    
    # Extracted information
    key_details: dict = Field(description="Important details extracted from email")
    requires_scheduling: bool = Field(description="Whether email mentions calendar events")
    calendar_event: Optional[dict] = Field(default=None, description="Extracted calendar event if any")
    
    # Actions
    draft_reply: Optional[str] = Field(default=None, description="Drafted reply if action is 'reply'")
    next_agent: Literal["scheduler_agent", "supervisor", "END"] = Field(
        default="supervisor",
        description="Next agent to route to"
    )


class SchedulerAgentResponse(BaseModel):
    """Scheduler agent actions"""
    action: Literal[
        "create_event",
        "update_event", 
        "delete_event",
        "list_events",
        "create_todo",
        "set_reminder",
        "check_conflicts"
    ] = Field(description="Calendar action to perform")
    
    event_details: Optional[dict] = Field(default=None)
    conflicts_found: bool = Field(default=False)
    conflict_details: list = Field(default_factory=list)
    suggestions: list = Field(default_factory=list)
    requires_human_decision: bool = Field(default=False)
    
    next_agent: Literal["human_review", "supervisor", "END"] = Field(default="supervisor")


class BookingAgentResponse(BaseModel):
    """Booking agent response"""
    booking_type: Literal["flight", "hotel", "train", "restaurant", "other"]
    search_performed: bool = Field(default=False)
    options_found: int = Field(default=0)
    top_recommendations: list = Field(default_factory=list)
    requires_more_info: bool = Field(default=False)
    missing_params: list = Field(default_factory=list)
    
    # Always requires human confirmation
    ready_for_booking: bool = Field(default=False)
    next_agent: Literal["human_review", "supervisor"] = Field(default="human_review")


class ChitChatResponse(BaseModel):
    """ChitChat agent response"""
    response_text: str = Field(description="Casual chat response")
    detected_intent: Optional[str] = Field(default=None, description="Underlying intent if detected")
    requires_escalation: bool = Field(default=False)
    escalate_to: Optional[Literal["email_agent", "scheduler_agent", "booking_agent"]] = Field(
        default=None
    )
    next_agent: Literal["email_agent", "scheduler_agent", "booking_agent", "supervisor", "END"] = Field(
        default="END"
    )


class HealthMonitorResponse(BaseModel):
    """Health and emotion analysis"""
    sentiment_score: float = Field(ge=-1, le=1, description="Overall sentiment -1 to 1")
    emotion_detected: Literal[
        "happy", "neutral", "stressed", "frustrated", "anxious", "excited", "tired", "angry"
    ]
    stress_level: float = Field(ge=0, le=1, description="Stress level 0 to 1")
    exhaustion_indicators: list = Field(default_factory=list)
    
    alert_level: Literal["normal", "concern", "alert"] = Field(default="normal")
    recommendations: list = Field(default_factory=list)
    should_suggest_break: bool = Field(default=False)
    
    # Insights
    conversation_patterns: dict = Field(default_factory=dict)
    trending_sentiment: str = Field(default="stable")