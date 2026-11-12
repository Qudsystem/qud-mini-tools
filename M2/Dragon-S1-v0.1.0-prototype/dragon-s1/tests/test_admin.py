from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models import User, Device, AccessRequest, SystemMetric, AuditLog


def test_admin_stats_unauthorized(client: TestClient):
    r = client.get("/api/admin/stats")
    assert r.status_code == 401


def test_admin_stats_authorized(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    r = client.get("/api/admin/stats", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "devices" in data
    assert "pending_requests" in data


def test_heartbeat_check(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    r = client.post("/api/admin/heartbeat-check", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "checked" in data
    assert "marked_offline" in data


def test_expire_sessions(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    r = client.post("/api/admin/expire-sessions", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "expired" in data


def test_cleanup_uploads(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    r = client.post("/api/admin/cleanup-uploads", headers=admin_headers)
    assert r.status_code == 200


def test_latest_events_unauthorized(client: TestClient):
    r = client.get("/api/admin/events/latest")
    assert r.status_code == 401


def test_latest_events_authorized(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    # Create some test audit logs
    db_session.add(AuditLog(actor="test_user", action="login", target_type="user", target_id="1", details="Test login"))
    db_session.add(AuditLog(actor="test_user", action="logout", target_type="user", target_id="1", details="Test logout"))
    db_session.commit()
    
    r = client.get("/api/admin/events/latest?limit=10", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "events" in data
    assert "total_count" in data
    assert isinstance(data["events"], list)
    assert len(data["events"]) <= 10
    assert data["total_count"] >= 2
    
    # Check event structure
    if len(data["events"]) > 0:
        event = data["events"][0]
        assert "id" in event
        assert "action" in event
        assert "action_ar" in event
        assert "actor" in event
        assert "created_at" in event
        assert "timestamp_relative" in event
        assert "icon_type" in event
        assert "icon_svg" in event


def test_latest_events_with_since(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    # Create audit logs
    db_session.add(AuditLog(actor="test_user", action="login", target_type="user", target_id="1", details="Test login"))
    db_session.commit()
    
    r = client.get("/api/admin/events/latest?limit=5", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    initial_count = len(data["events"])
    
    # Use since parameter to filter
    if initial_count > 0:
        since_time = data["events"][0]["created_at"]
        r2 = client.get(f"/api/admin/events/latest?since={since_time}", headers=admin_headers)
        assert r2.status_code == 200
        data2 = r2.json()
        # Should return fewer or equal events
        assert len(data2["events"]) <= initial_count


def test_latest_events_limit_validation(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    # Test with limit > 100 (should be capped at 100)
    r = client.get("/api/admin/events/latest?limit=200", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert len(data["events"]) <= 100
    
    # Test with limit < 1 (should be set to 1)
    r = client.get("/api/admin/events/latest?limit=0", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert len(data["events"]) <= 1
