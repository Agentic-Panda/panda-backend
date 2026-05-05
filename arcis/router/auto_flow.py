from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from arcis.core.llm.pending_interrupt import (
    get_all_pending,
    get_all_interrupts,
    get_pending_count,
    get_pending_by_id,
    dismiss_pending,
)
from arcis.core.workflow_auto.auto_flow import resolve_interrupt

auto_flow_router = APIRouter(prefix="/auto_flow", tags=["Auto Flow"])


# --- Models ---

class PendingItemSchema(BaseModel):
    id: str = Field(..., alias="_id")
    thread_id: str
    question: str
    status: str
    source_context: dict = {}
    created_at: float

    class Config:
        populate_by_name = True

class PendingCountSchema(BaseModel):
    pending: int
    total: int

class ResolveRequest(BaseModel):
    interrupt_id: str
    answer: str

class DismissRequest(BaseModel):
    interrupt_id: str

class ResolveResponse(BaseModel):
    status: str
    message: str
    workflow_status: Optional[str] = None


# --- Endpoints ---

@auto_flow_router.get("/pending", response_model=List[PendingItemSchema])
async def get_pending_items():
    """List all pending (unresolved) interrupt items."""
    return get_all_pending()


@auto_flow_router.get("/interrupts", response_model=List[PendingItemSchema])
async def list_interrupts(
    status: Optional[str] = Query(None, description="Filter by status: pending, resolved, dismissed"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=200, description="Max items to return"),
):
    """
    List all interrupts with optional filtering and pagination.
    Useful for a history/log view in the frontend.
    
    - **status**: Filter by `pending`, `resolved`, or `dismissed`. Omit for all.
    - **skip** / **limit**: Pagination.
    """
    return get_all_interrupts(status=status, skip=skip, limit=limit)


@auto_flow_router.get("/interrupts/count", response_model=PendingCountSchema)
async def get_interrupt_count():
    """
    Return the count of pending (unresolved) interrupts and total interrupts.
    Useful for badge/notification indicators in the frontend.
    """
    return get_pending_count()


@auto_flow_router.get("/interrupts/{interrupt_id}", response_model=PendingItemSchema)
async def get_interrupt_detail(interrupt_id: str):
    """Get a single interrupt item by its ID."""
    doc = get_pending_by_id(interrupt_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Interrupt not found")
    return doc


@auto_flow_router.post("/resolve", response_model=ResolveResponse)
async def resolve_pending_item(request: ResolveRequest):
    """Provide an answer to a pending interrupt, resuming the workflow."""
    try:
        result = await resolve_interrupt(request.interrupt_id, request.answer)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@auto_flow_router.post("/dismiss", response_model=ResolveResponse)
async def dismiss_pending_item(request: DismissRequest):
    """Dismiss a pending interrupt (user chooses to skip)."""
    try:
        dismiss_pending(request.interrupt_id)
        return {"status": "dismissed", "message": "Item dismissed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
