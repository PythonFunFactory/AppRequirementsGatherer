import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from ..database import get_db
from ..models import Session as SessionModel, Message, MessageRole, User, SessionStatus
from ..schemas.message import MessageCreate
from ..services.auth_service import get_current_user
from ..services.claude_service import stream_response

router = APIRouter(prefix="/sessions", tags=["messages"])


@router.post("/{session_id}/messages")
async def send_message(
    session_id: int,
    body: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id, SessionModel.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Persist user message
    user_msg = Message(session_id=session_id, role=MessageRole.user, content=body.content)
    db.add(user_msg)
    db.commit()

    # Auto-title the session from first user message
    if session.title == "New Session":
        session.title = body.content[:60].rstrip() + ("…" if len(body.content) > 60 else "")
        db.commit()

    # Build message history for Claude
    all_messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.created_at).all()
    claude_messages = [{"role": m.role.value, "content": m.content} for m in all_messages]

    # Stream response and accumulate for DB persistence
    async def event_stream():
        accumulated = []
        try:
            async for chunk in stream_response(claude_messages):
                accumulated.append(chunk)
                yield f"data: {json.dumps({'text': chunk})}\n\n"
        finally:
            # Persist assistant response after streaming completes
            full_response = "".join(accumulated)
            if full_response:
                assistant_msg = Message(
                    session_id=session_id,
                    role=MessageRole.assistant,
                    content=full_response,
                )
                db.add(assistant_msg)
                session.updated_at = datetime.now(timezone.utc)
                db.commit()
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
