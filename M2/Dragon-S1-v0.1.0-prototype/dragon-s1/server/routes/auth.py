from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import AuditLog, User
from schemas import LoginIn, MFAVerifyIn
from security import create_token, verify_password, decode_token
from mfa import verify_mfa_code

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/login",
    summary="User Login",
    description="Authenticates a user and returns an access token or an MFA required response.",
    responses={
        200: {"description": "Successful login or MFA required token"},
        401: {"description": "Invalid username or password"},
        403: {"description": "Account disabled"}
    }
)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == data.username))
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    if not user.is_active or user.is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
        
    if user.mfa_secret:
        # Require MFA, issue temporary token
        temp_token = create_token(user.username, "mfa_pending", minutes=5)
        return {"mfa_required": True, "temp_token": temp_token}

    # Update last login timestamp
    user.last_login = datetime.now(timezone.utc)
    db.add(user)
    
    db.add(AuditLog(actor=user.username, action="login", target_type="user", target_id=str(user.id)))
    db.commit()
    return {
        "access_token": create_token(user.username, user.role),
        "token_type": "bearer",
        "user": {"username": user.username, "full_name": user.full_name, "role": user.role},
    }

@router.post(
    "/verify-mfa",
    summary="Verify MFA Code",
    description="Verifies the MFA code using a temporary token from login.",
    responses={
        200: {"description": "MFA verified, returns access token"},
        401: {"description": "Invalid token or MFA code"}
    }
)
def verify_mfa(data: MFAVerifyIn, db: Session = Depends(get_db)):
    try:
        payload = decode_token(data.temp_token)
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired temporary token")
        
    if payload.get("role") != "mfa_pending":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        
    username = payload.get("sub")
    user = db.scalar(select(User).where(User.username == username))
    
    if not user or not user.mfa_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="MFA not configured for this user")
        
    if not verify_mfa_code(user.mfa_secret, data.mfa_code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA code")
        
    # Update last login timestamp
    user.last_login = datetime.now(timezone.utc)
    db.add(user)
    
    db.add(AuditLog(actor=user.username, action="login_mfa", target_type="user", target_id=str(user.id)))
    db.commit()
    return {
        "access_token": create_token(user.username, user.role),
        "token_type": "bearer",
        "user": {"username": user.username, "full_name": user.full_name, "role": user.role},
    }
