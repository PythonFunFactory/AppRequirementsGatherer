from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    user = "user"
    admin = "admin"


class UserOut(BaseModel):
    id: int
    email: str
    display_name: str
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}
