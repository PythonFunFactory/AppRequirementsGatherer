from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import httpx

from ..config import settings
from ..database import get_db
from ..services.auth_service import (
    create_access_token,
    get_or_create_user,
    get_current_user,
)
from ..schemas.user import UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

ENTRA_AUTHORIZE_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
ENTRA_TOKEN_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
REDIRECT_URI = "http://localhost:8000/auth/callback"


class DevLoginRequest(BaseModel):
    email: str
    display_name: str = "Dev User"
    role: str = "user"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.get("/login")
async def login():
    if settings.dev_auth:
        raise HTTPException(status_code=400, detail="Use /auth/dev-login in dev mode")
    params = {
        "client_id": settings.azure_client_id,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": "openid profile email",
        "response_mode": "query",
    }
    url = ENTRA_AUTHORIZE_URL.format(tenant=settings.azure_tenant_id)
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(f"{url}?{query}")


@router.get("/callback")
async def callback(code: str, response: Response, db: Session = Depends(get_db)):
    token_url = ENTRA_TOKEN_URL.format(tenant=settings.azure_tenant_id)
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(token_url, data={
            "client_id": settings.azure_client_id,
            "client_secret": settings.azure_client_secret,
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        })
    token_data = token_resp.json()
    if "error" in token_data:
        raise HTTPException(status_code=400, detail=token_data.get("error_description", "Auth failed"))

    # Decode the ID token to get user info (without full validation for brevity;
    # production should validate signature against Entra ID JWKS)
    import base64, json
    id_token = token_data["id_token"]
    parts = id_token.split(".")
    padding = 4 - len(parts[1]) % 4
    claims = json.loads(base64.urlsafe_b64decode(parts[1] + "=" * padding))

    email = claims.get("email") or claims.get("preferred_username", "")
    display_name = claims.get("name", email)
    entra_id = claims.get("oid")

    user = get_or_create_user(db, email, display_name, entra_id)
    access_token = create_access_token({"sub": str(user.id)})

    response.set_cookie("access_token", access_token, httponly=True, samesite="lax", max_age=28800)
    return RedirectResponse(settings.frontend_url)


@router.post("/dev-login", response_model=TokenResponse)
async def dev_login(body: DevLoginRequest, response: Response, db: Session = Depends(get_db)):
    if not settings.dev_auth:
        raise HTTPException(status_code=403, detail="Dev login is disabled")
    from ..models import UserRole
    override_role = UserRole.admin if body.email.lower() in settings.admin_email_list else UserRole(body.role)
    user = get_or_create_user(db, body.email, body.display_name)
    # Allow role override for dev convenience
    if user.role != override_role:
        user.role = override_role
        db.commit()
        db.refresh(user)
    access_token = create_access_token({"sub": str(user.id)})
    response.set_cookie("access_token", access_token, httponly=True, samesite="lax", max_age=28800)
    return TokenResponse(access_token=access_token)


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"ok": True}


@router.get("/me", response_model=UserOut)
async def me(current_user=Depends(get_current_user)):
    return current_user
