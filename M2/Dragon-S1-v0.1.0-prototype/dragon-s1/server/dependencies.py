from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import User
from security import decode_token

bearer = HTTPBearer(auto_error=True)


def token_payload(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    return decode_token(credentials.credentials)


def require_admin(payload: dict = Depends(token_payload), db: Session = Depends(get_db)) -> User:
    if payload.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    user = db.scalar(select(User).where(User.username == payload.get("sub")))
    if not user or not user.is_active or user.is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    return user


def require_agent(payload: dict = Depends(token_payload)) -> dict:
    if payload.get("role") != "agent":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agent access required")
    return payload


def get_current_user(payload: dict = Depends(token_payload), db: Session = Depends(get_db)) -> User:
    user = db.scalar(select(User).where(User.username == payload.get("sub")))
    if not user or not user.is_active or user.is_blocked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials or account disabled")
    return user

