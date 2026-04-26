import os
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Session as SessionModel, Message, User, PdfRecord, SessionStatus
from ..schemas.pdf import PdfOut
from ..services.auth_service import get_current_user
from ..services.claude_service import generate_requirements_json
from ..services.pdf_service import render_pdf

router = APIRouter(prefix="/sessions", tags=["pdfs"])


@router.post("/{session_id}/pdf", response_model=PdfOut)
async def generate_pdf(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id, SessionModel.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.created_at).all()
    if not messages:
        raise HTTPException(status_code=400, detail="No messages in session")

    claude_messages = [{"role": m.role.value, "content": m.content} for m in messages]
    requirements = await generate_requirements_json(claude_messages)

    tech_stack = requirements.pop("tech_stack_suggestions", {})
    file_path = await render_pdf(session_id, requirements, session.title)

    pdf_record = db.query(PdfRecord).filter(PdfRecord.session_id == session_id).first()
    if pdf_record:
        pdf_record.file_path = file_path
        pdf_record.tech_stack_json = json.dumps(tech_stack)
    else:
        pdf_record = PdfRecord(
            session_id=session_id,
            file_path=file_path,
            tech_stack_json=json.dumps(tech_stack),
        )
        db.add(pdf_record)

    session.status = SessionStatus.complete
    db.commit()
    db.refresh(pdf_record)
    return pdf_record


@router.get("/{session_id}/pdf")
def download_pdf(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id, SessionModel.user_id == current_user.id
    ).first()
    if not session or not session.pdf:
        raise HTTPException(status_code=404, detail="PDF not found")

    file_path = session.pdf.file_path

    if file_path.startswith("s3://"):
        import boto3
        s3_key = file_path[len("s3://"):]
        url = boto3.client("s3", region_name=settings.aws_region).generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.aws_s3_bucket,
                "Key": s3_key,
                "ResponseContentDisposition": f"attachment; filename=requirements-{session_id}.pdf",
            },
            ExpiresIn=300,
        )
        return RedirectResponse(url)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF file missing from disk")
    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=f"requirements-{session_id}.pdf",
    )
