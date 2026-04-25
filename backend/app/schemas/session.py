from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import List, Optional
from .message import MessageOut
from .user import UserOut


class SessionStatus(str, Enum):
    active = "active"
    complete = "complete"


class SessionCreate(BaseModel):
    pass


class SessionOut(BaseModel):
    id: int
    title: str
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    has_pdf: bool = False

    model_config = {"from_attributes": True}


class SessionDetail(SessionOut):
    messages: List[MessageOut] = []
    user: Optional[UserOut] = None
