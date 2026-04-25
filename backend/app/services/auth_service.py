from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import httpx

from ..config import settings
from ..database import get_db
from ..models import User, UserRole

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

security = HTTPBearer(auto_error=False)

# Entra ID JWKS cache
_jwks_cache: Optional[dict] = None
_jwks_fetched_at: Optional[datetime] = None


def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def get_entra_public_keys() -> dict:
    global _jwks_cache, _jwks_fetched_at
    now = datetime.now(timezone.utc)
    if _jwks_cache and _jwks_fetched_at and (now - _jwks_fetched_at).seconds < 3600:
        return _jwks_cache
    async with httpx.AsyncClient() as client:
        oidc_config = await client.get(
            f"https://login.microsoftonline.com/{settings.azure_tenant_id}/v2.0/.well-known/openid-configuration"
        )
        jwks_uri = oidc_config.json()["jwks_uri"]
        jwks_resp = await client.get(jwks_uri)
        _jwks_cache = jwks_resp.json()
        _jwks_fetched_at = now
    return _jwks_cache


def get_or_create_user(db: Session, email: str, display_name: str, entra_id: Optional[str] = None) -> User:
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user:
        role = UserRole.admin if email.lower() in settings.admin_email_list else UserRole.user
        user = User(email=email.lower(), display_name=display_name, entra_id=entra_id, role=role)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_token_from_request(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    access_token: Optional[str] = Cookie(default=None),
) -> Optional[str]:
    if credentials:
        return credentials.credentials
    return access_token


def get_current_user(
    token: Optional[str] = Depends(get_token_from_request),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user
