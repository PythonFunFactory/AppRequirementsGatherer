from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PdfOut(BaseModel):
    id: int
    session_id: int
    generated_at: datetime

    model_config = {"from_attributes": True}
