from typing import TypedDict, Annotated, List, Optional
import operator
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class MasterState(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    next_step: Optional[str]
    
    # GLOBAL CONTEXT: Shared data accessible by all agents
    # (Useful so the Booking agent knows who the 'current_user' is)
    #user_profile: Optional[dict] 
    #current_time: str

class ProductivityState(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    internal_decision: Optional[str]