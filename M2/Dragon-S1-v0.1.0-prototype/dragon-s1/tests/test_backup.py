from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models import User


def test_list_backups_unauthorized(client: TestClient):
    r = client.get("/api/backup")
    assert r.status_code == 401


def test_list_backups_empty(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    r = client.get("/api/backup", headers=admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_backup(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    r = client.post("/api/backup", headers=admin_headers, json={"backup_type": "full"})
    assert r.status_code in (200, 201)
    data = r.json()
    assert "filename" in data or "ok" in data


def test_verify_backup(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    # First create a backup
    create_r = client.post("/api/backup", headers=admin_headers, json={"backup_type": "full"})
    assert create_r.status_code in (200, 201)
    
    # Then list it
    list_r = client.get("/api/backup", headers=admin_headers)
    backups = list_r.json()
    if backups:
        bid = backups[0]["id"]
        verify_r = client.post(f"/api/backup/{bid}/verify", headers=admin_headers)
        assert verify_r.status_code == 200
