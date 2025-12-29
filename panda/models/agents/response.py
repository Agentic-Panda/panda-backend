from typing import Literal
from pydantic import BaseModel, Field


class SupervisorRouterResponse(BaseModel):
    next_step: Literal["PRODUCTIVITY", "OPERATIONS", "HEALTH", "SCRIBE"] = Field(
        ...,
        description="The next step to route the user to."
    )

class ProductivityRouterResponse(BaseModel):
    next_step: Literal["EMAIL_AGENT", "SCHEDULER_AGENT"] = Field(
        description="The specific agent to handle the user request."
    )