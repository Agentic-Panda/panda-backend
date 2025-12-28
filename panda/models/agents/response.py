from typing import Literal
from pydantic import BaseModel, Field


class SupervisorRouterResponse(BaseModel):
    next_step: Literal["PRODUCTIVITY", "OPERATIONS", "HEALTH", "SCRIBE"] = Field(
        ...,
        description="The next step to route the user to."
    )