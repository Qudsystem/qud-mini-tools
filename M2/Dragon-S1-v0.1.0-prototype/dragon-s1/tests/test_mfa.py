import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from main import app
from database import get_db
from models import User
from security import hash_password
from mfa import generate_mfa_secret
import pyotp

def test_mfa_login_flow(db_session: Session, client: TestClient):
    
    # Create user with MFA
    secret = generate_mfa_secret()
    user = User(
        username="mfa_user",
        password_hash=hash_password("password123"),
        full_name="MFA User",
        role="admin",
        mfa_secret=secret
    )
    db_session.add(user)
    db_session.commit()
    
    # Step 1: Login to get temp_token
    response = client.post("/api/auth/login", json={"username": "mfa_user", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert data.get("mfa_required") is True
    temp_token = data.get("temp_token")
    assert temp_token is not None
    
    # Step 2: Verify MFA with correct code
    totp = pyotp.TOTP(secret)
    valid_code = totp.now()
    
    response2 = client.post("/api/auth/verify-mfa", json={
        "temp_token": temp_token,
        "mfa_code": valid_code
    })
    assert response2.status_code == 200
    data2 = response2.json()
    assert "access_token" in data2
    assert data2["user"]["username"] == "mfa_user"
    
    # Step 3: Verify MFA with wrong code
    response3 = client.post("/api/auth/verify-mfa", json={
        "temp_token": temp_token,
        "mfa_code": "000000"
    })
    assert response3.status_code == 401
