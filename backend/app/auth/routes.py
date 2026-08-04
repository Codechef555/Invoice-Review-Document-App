from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.config import get_settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


class PasswordVerifyRequest(BaseModel):
    password: str


class PasswordVerifyResponse(BaseModel):
    success: bool
    message: str


@router.post("/verify", response_model=PasswordVerifyResponse)
def verify_password(payload: PasswordVerifyRequest) -> PasswordVerifyResponse:
    settings = get_settings()
    if payload.password == settings.app_password:
        return PasswordVerifyResponse(success=True, message="Authenticated successfully")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid passcode",
    )
