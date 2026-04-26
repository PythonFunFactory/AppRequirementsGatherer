import json
import os
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models import Session as SessionModel, Message, User
from ..schemas.session import SessionOut, SessionDetail
from ..schemas.user import UserOut
from ..services.auth_service import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


def session_to_out(s: SessionModel) -> SessionOut:
    return SessionOut(
        id=s.id,
        title=s.title,
        status=s.status,
        created_at=s.created_at,
        updated_at=s.updated_at,
        has_pdf=s.pdf is not None,
    )


@router.get("/sessions", response_model=List[SessionOut])
def admin_list_sessions(
    user_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    query = db.query(SessionModel)
    if user_id:
        query = query.filter(SessionModel.user_id == user_id)
    if status:
        query = query.filter(SessionModel.status == status)
    sessions = query.order_by(SessionModel.updated_at.desc()).all()
    return [session_to_out(s) for s in sessions]


class AdminSessionDetail(SessionDetail):
    tech_stack: Optional[dict] = None


@router.get("/sessions/{session_id}")
def admin_get_session(
    session_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    tech_stack = None
    if session.pdf and session.pdf.tech_stack_json:
        tech_stack = json.loads(session.pdf.tech_stack_json)

    return {
        "id": session.id,
        "title": session.title,
        "status": session.status,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "has_pdf": session.pdf is not None,
        "user": {
            "id": session.user.id,
            "email": session.user.email,
            "display_name": session.user.display_name,
        },
        "messages": [
            {"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at}
            for m in session.messages
        ],
        "tech_stack": tech_stack,
    }


@router.get("/sessions/{session_id}/pdf")
def admin_download_pdf(
    session_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session or not session.pdf:
        raise HTTPException(status_code=404, detail="PDF not found")
    if not os.path.exists(session.pdf.file_path):
        raise HTTPException(status_code=404, detail="PDF file missing from disk")
    return FileResponse(
        session.pdf.file_path,
        media_type="application/pdf",
        filename=f"requirements-{session_id}.pdf",
    )


@router.get("/users", response_model=List[UserOut])
def admin_list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(User).order_by(User.created_at.desc()).all()
