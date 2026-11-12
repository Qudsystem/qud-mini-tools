from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models import User, Device, AccessRequest
from datetime import datetime, date, timedelta, timezone


def test_daily_report_unauthorized(client: TestClient):
    r = client.get("/api/reports/daily?date=2026-06-27")
    assert r.status_code == 401


def test_daily_report_empty(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    today = date.today().isoformat()
    r = client.get(f"/api/reports/daily?date={today}", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "summary" in data
    assert "requests_count" in data


def test_weekly_report(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    today = date.today().isoformat()
    r = client.get(f"/api/reports/weekly?start={today}", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "summary" in data


def test_custom_report(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    today = date.today().isoformat()
    r = client.post("/api/reports/custom/export", headers=admin_headers, json={
        "start_date": today,
        "end_date": today,
        "format": "pdf",
        "filters": {}
    })
    assert r.status_code == 200


def test_schedule_report(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    r = client.post("/api/reports/schedule", headers=admin_headers, json={
        "name": "Test Daily Report",
        "frequency": "daily",
        "format": "csv",
        "recipients": ["admin@example.com"],
        "filters": {}
    })
    assert r.status_code in (200, 201)


def test_list_scheduled_reports(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    r = client.get("/api/reports/schedule", headers=admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)
