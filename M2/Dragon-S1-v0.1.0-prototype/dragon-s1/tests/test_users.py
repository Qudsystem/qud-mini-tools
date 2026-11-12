from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models import User


def test_list_users_unauthorized(client: TestClient):
    r = client.get("/api/users")
    assert r.status_code == 401


def test_list_users(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    r = client.get("/api/users", headers=admin_headers)
    assert r.status_code == 200
    users = r.json()
    assert isinstance(users, list)
    assert any(u["username"] == "testadmin" for u in users)


def test_create_user(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    r = client.post("/api/users", headers=admin_headers, json={
        "username": "newuser",
        "full_name": "New User",
        "password": "StrongPass123!",
        "role": "operator",
        "department": "IT"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["username"] == "newuser"
    assert data["role"] == "operator"


def test_create_duplicate_user(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    r = client.post("/api/users", headers=admin_headers, json={
        "username": "testadmin",
        "full_name": "Duplicate",
        "password": "strongpassword123",
        "role": "viewer",
        "department": ""
    })
    assert r.status_code == 409


def test_change_user_role(client: TestClient, db_session: Session, test_admin: User, test_operator: User, admin_headers: dict):
    r = client.put(f"/api/users/{test_operator.id}/role", headers=admin_headers, json={"role": "viewer"})
    assert r.status_code == 200
    assert r.json()["role"] == "viewer"


def test_block_user(client: TestClient, db_session: Session, test_admin: User, test_operator: User, admin_headers: dict):
    r = client.patch(f"/api/users/{test_operator.id}/blocked", headers=admin_headers, json={"blocked": True})
    assert r.status_code == 200
    assert r.json()["is_blocked"] == True


def test_delete_user(client: TestClient, db_session: Session, test_admin: User, test_operator: User, admin_headers: dict):
    r = client.delete(f"/api/users/{test_operator.id}", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["ok"] == True


def test_delete_self_forbidden(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    r = client.delete(f"/api/users/{test_admin.id}", headers=admin_headers)
    assert r.status_code == 400
