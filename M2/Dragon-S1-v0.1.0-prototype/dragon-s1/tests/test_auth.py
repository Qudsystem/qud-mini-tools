from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models import User
from security import hash_password


def test_login_success(client: TestClient, test_admin: User):
    response = client.post("/api/auth/login", json={"username": "testadmin", "password": "adminpass123"})
    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    assert json_data["token_type"] == "bearer"
    # Wait, the auth payload return scheme in auth.py has "access_token" and "token_type", let's check
    # In auth.py it returns: {"access_token": create_token(...), "token_type": "bearer", "user": {...}}
    # So "role" is inside "user"! Let's check assert
    assert "user" in json_data
    assert json_data["user"]["role"] == "admin"


def test_login_wrong_password(client: TestClient, test_admin: User):
    response = client.post("/api/auth/login", json={"username": "testadmin", "password": "wrongpassword"})
    assert response.status_code == 401
    assert "detail" in response.json()


def test_login_nonexistent_user(client: TestClient):
    response = client.post("/api/auth/login", json={"username": "nouser", "password": "somepassword"})
    assert response.status_code == 401
    assert "detail" in response.json()


def test_login_blocked_user(client: TestClient, db_session: Session):
    blocked_user = User(
        username="blocked",
        full_name="Blocked User",
        password_hash=hash_password("password123"),
        role="viewer",
        is_active=True,
        is_blocked=True
    )
    db_session.add(blocked_user)
    db_session.commit()

    response = client.post("/api/auth/login", json={"username": "blocked", "password": "password123"})
    assert response.status_code == 403
    assert "disabled" in response.json()["detail"].lower()


def test_login_inactive_user(client: TestClient, db_session: Session):
    inactive_user = User(
        username="inactive",
        full_name="Inactive User",
        password_hash=hash_password("password123"),
        role="viewer",
        is_active=False
    )
    db_session.add(inactive_user)
    db_session.commit()

    response = client.post("/api/auth/login", json={"username": "inactive", "password": "password123"})
    assert response.status_code == 403
    assert "disabled" in response.json()["detail"].lower()


