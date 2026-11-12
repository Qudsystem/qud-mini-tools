from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models import User, Notification


def test_list_notifications_unauthorized(client: TestClient):
    r = client.get("/api/notifications")
    assert r.status_code == 401


def test_list_notifications_empty(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    r = client.get("/api/notifications", headers=admin_headers)
    assert r.status_code == 200
    assert r.json() == []


def test_list_notifications_with_data(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    import json
    notif = Notification(
        channel="dashboard",
        severity="info",
        title="Test Notification",
        message="Hello World",
        data=json.dumps({"key": "value"}),
        is_read=False,
    )
    db_session.add(notif)
    db_session.commit()
    db_session.refresh(notif)
    
    r = client.get("/api/notifications", headers=admin_headers)
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1
    assert items[0]["title"] == "Test Notification"


def test_unread_count(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    r = client.get("/api/notifications/unread-count", headers=admin_headers)
    assert r.status_code == 200
    assert "unread_count" in r.json()


def test_mark_notification_read(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    import json
    notif = Notification(
        channel="dashboard",
        severity="info",
        title="Mark Read Test",
        message="Test",
        data=json.dumps({}),
        is_read=False,
    )
    db_session.add(notif)
    db_session.commit()
    db_session.refresh(notif)
    
    r = client.put(f"/api/notifications/{notif.id}/read", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["ok"] == True


def test_delete_notification(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    import json
    notif = Notification(
        channel="dashboard",
        severity="info",
        title="Delete Test",
        message="Test",
        data=json.dumps({}),
    )
    db_session.add(notif)
    db_session.commit()
    db_session.refresh(notif)
    
    r = client.delete(f"/api/notifications/{notif.id}", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["ok"] == True
