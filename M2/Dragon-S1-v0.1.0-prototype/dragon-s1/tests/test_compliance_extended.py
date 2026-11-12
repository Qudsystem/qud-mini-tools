from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models import User, AuditLog


def test_verify_audit_trail_empty(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    r = client.get("/api/compliance/verify", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "integrity_verified" in data


def test_get_audit_logs(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    # Create some audit logs
    db_session.add(AuditLog(actor="testadmin", action="test_action", target_type="test", target_id="1"))
    db_session.commit()
    
    r = client.get("/api/compliance/logs?page=1&page_size=10", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "items" in data or isinstance(data, list)


def test_export_compliance_logs_json(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    r = client.get("/api/compliance/export?format=json", headers=admin_headers)
    assert r.status_code == 200
    assert "application/json" in r.headers.get("content-type", "")


def test_export_compliance_logs_csv(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    r = client.get("/api/compliance/export?format=csv", headers=admin_headers)
    assert r.status_code == 200
    assert "text/csv" in r.headers.get("content-type", "")
