from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Session as SessionModel, User
from ..schemas.session import SessionOut, SessionDetail, SessionCreate
from ..services.auth_service import get_current_user

router = APIRouter(prefix="/sessions", tags=["sessions"])


def session_to_out(s: SessionModel) -> SessionOut:
    return SessionOut(
        id=s.id,
        title=s.title,
        status=s.status,
        created_at=s.created_at,
        updated_at=s.updated_at,
        has_pdf=s.pdf is not None,
    )


@router.get("", response_model=List[SessionOut])
def list_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sessions = db.query(SessionModel).filter(SessionModel.user_id == current_user.id).order_by(SessionModel.updated_at.desc()).all()
    return [session_to_out(s) for s in sessions]


@router.post("", response_model=SessionOut)
def create_session(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = SessionModel(user_id=current_user.id, title="New Session")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session_to_out(session)


@router.get("/{session_id}", response_model=SessionDetail)
def get_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id, SessionModel.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionDetail(
        id=session.id,
        title=session.title,
        status=session.status,
        created_at=session.created_at,
        updated_at=session.updated_at,
        has_pdf=session.pdf is not None,
        messages=session.messages,
    )


@router.delete("/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id, SessionModel.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return {"ok": True}
