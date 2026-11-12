from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models import User, WebhookSubscription


def test_list_webhooks_unauthorized(client: TestClient):
    r = client.get("/api/webhooks")
    assert r.status_code == 401


def test_list_webhooks_empty(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    r = client.get("/api/webhooks", headers=admin_headers)
    assert r.status_code == 200
    assert r.json() == []


def test_subscribe_webhook(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    r = client.post("/api/webhooks/subscribe", headers=admin_headers, json={
        "url": "https://example.com/webhook",
        "secret_token": "mysecret",
        "events": ["request.created", "request.decided"]
    })
    assert r.status_code == 201
    data = r.json()
    assert data["ok"] == True
    assert "id" in data


def test_list_webhooks_with_data(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    import json
    sub = WebhookSubscription(
        url="https://test.com/hook",
        secret_token="token123",
        events=json.dumps(["*"]),
        is_active=True
    )
    db_session.add(sub)
    db_session.commit()
    db_session.refresh(sub)
    
    r = client.get("/api/webhooks", headers=admin_headers)
    assert r.status_code == 200
    items = r.json()
    assert any(item["url"] == "https://test.com/hook" for item in items)


def test_unsubscribe_webhook(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    import json
    sub = WebhookSubscription(
        url="https://delete.me/hook",
        events=json.dumps(["*"]),
        is_active=True
    )
    db_session.add(sub)
    db_session.commit()
    db_session.refresh(sub)
    
    r = client.delete(f"/api/webhooks/{sub.id}", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["ok"] == True
