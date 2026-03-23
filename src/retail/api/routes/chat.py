from __future__ import annotations

import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, HTTPException, Request, WebSocket
from pydantic import BaseModel

from retail.assistant.assistant import ShoppingAssistant
from retail.assistant.domain import ConversationContext
from retail.recommendations.domain import RecommendationRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


class ChatStartResponse(BaseModel):
    session_id: str
    message: str


@router.post("/chat/start", response_model=ChatStartResponse)
async def start_chat(customer_id: str, request: Request) -> ChatStartResponse:
    """Create a new chat session."""
    profile = request.app.state.profiles_by_id.get(customer_id)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    req = RecommendationRequest(customer_id=customer_id, top_n=5)
    recs = request.app.state.engine.predict(req)

    session_id = str(uuid.uuid4())
    ctx = ConversationContext(
        session_id=session_id,
        profile=profile,
        recommendations=recs,
    )
    request.app.state.sessions[session_id] = ctx
    return ChatStartResponse(
        session_id=session_id,
        message=f"Session {session_id} started for customer {customer_id}",
    )


@router.websocket("/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str) -> None:
    """WebSocket endpoint for streaming chat."""
    await websocket.accept()
    ctx = websocket.app.state.sessions.get(session_id)
    if ctx is None:
        await websocket.send_text("Session not found.")
        await websocket.close()
        return

    assistant = ShoppingAssistant(catalogue=websocket.app.state.catalogue)
    try:
        while True:
            text = await websocket.receive_text()
            response = await asyncio.to_thread(assistant.chat, ctx, text)
            await websocket.send_text(
                json.dumps({
                    "message": response.message,
                    "pills": response.pills,
                    "cart": ctx.basket,
                    "receipt": ctx.last_order,
                })
            )
            ctx.last_order = None
    except Exception as exc:
        logger.exception("WebSocket chat error")
        try:
            await websocket.send_text(f"[Error] {exc}")
        except Exception:
            pass
