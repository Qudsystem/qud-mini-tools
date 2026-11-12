from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models import SystemMetric, User


def test_get_metrics_unauthorized(client: TestClient):
    """Metrics endpoint requires authentication."""
    r = client.get("/api/admin/metrics")
    assert r.status_code == 401


def test_get_metrics_empty(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    """Metrics endpoint returns empty series if no metrics stored."""
    r = client.get("/api/admin/metrics", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "cpu" in data
    assert "memory" in data
    assert "disk" in data
    assert data["cpu"] == []


def test_get_metrics_with_data(client: TestClient, db_session: Session, test_admin: User, admin_headers: dict):
    """Metrics endpoint returns recorded metrics correctly."""
    from datetime import datetime, timezone
    db_session.add(SystemMetric(metric_name="cpu_percent", value=42.5, unit="%"))
    db_session.add(SystemMetric(metric_name="memory_percent", value=65.0, unit="%"))
    db_session.add(SystemMetric(metric_name="disk_percent", value=30.0, unit="%"))
    db_session.commit()
    
    r = client.get("/api/admin/metrics?minutes=60", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert len(data["cpu"]) == 1
    assert data["cpu"][0]["value"] == 42.5
    assert len(data["memory"]) == 1
    assert len(data["disk"]) == 1
