from __future__ import annotations

import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

router = APIRouter(tags=["chat"])


class ChatStartResponse(BaseModel):
    session_id: str
    message: str


@router.post("/chat/start", response_model=ChatStartResponse)
async def start_chat(customer_id: str = "CUS_00000001") -> ChatStartResponse:
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    return ChatStartResponse(
        session_id=session_id,
        message=f"Session {session_id} started for customer {customer_id}",
    )


@router.websocket("/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str) -> None:
    """WebSocket endpoint for streaming chat."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Echo for now; wire up ShoppingAssistant in production
            await websocket.send_text(
                f"[Session {session_id}] Echo: {data}\n"
                "(Wire up ShoppingAssistant + ANTHROPIC_API_KEY for full chat)"
            )
    except WebSocketDisconnect:
        pass
