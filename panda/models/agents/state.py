from typing import TypedDict, Annotated, Literal, Optional
from datetime import datetime
import operator

class MasterStateRequired(TypedDict):
    messages: Annotated[list, operator.add]
    current_agent: str
    user_id: str
    conversation_id: str
    timestamp: datetime


class MasterState(MasterStateRequired, total=False):
    next_agent: Optional[str]

    # Context and actions
    context: dict
    pending_actions: Annotated[list, operator.add]

    # Human in loop
    requires_human: bool
    human_feedback: Optional[str]

    # Health monitoring
    interaction_history: Annotated[list, operator.add]
    emotion_state: dict
    stress_level: float

    # Agent-specific data
    email_data: Optional[dict]
    scheduler_data: Optional[dict]
    booking_data: Optional[dict]

    # Metadata
    session_metadata: dict


class EmailState(TypedDict):
    """Email agent specific state"""
    unprocessed_emails: list
    processed_email_ids: list
    drafted_replies: list
    emails_to_send: list
    spam_count: int
    important_emails: list
    extracted_actions: list


class SchedulerState(TypedDict):
    """Scheduler agent specific state"""
    calendar_events: list
    todos: list
    reminders: list
    conflicts: list
    suggestions: list


class BookingState(TypedDict):
    """Booking agent specific state"""
    booking_type: Literal["flight", "hotel", "train", "restaurant"]
    search_params: dict
    search_results: list
    selected_option: Optional[dict]
    booking_status: str
    confirmation_details: Optional[dict]


class HealthMetrics(TypedDict):
    """Health monitoring metrics"""
    sentiment_score: float  # -1 to 1
    stress_indicators: list
    exhaustion_level: float  # 0 to 1
    conversation_tone: str
    recommendations: list
    alert_level: Literal["normal", "concern", "alert"]