import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timezone
import io

from main import app
from database import get_db
from models import Device, AuditLog
from security import create_token

def test_periodic_check_endpoint(db_session: Session, client: TestClient):
    
    # Register device
    device = Device(
        device_uid="PC-12345-PERIODIC",
        hostname="TEST-PC",
        is_online=True
    )
    db_session.add(device)
    db_session.commit()
    
    agent_token = create_token("PC-12345-PERIODIC", "agent", minutes=60)
    
    # Create fake image
    fake_img = io.BytesIO(b"fake image data")
    fake_img.name = "test.jpg"
    
    response = client.post(
        "/api/devices/PC-12345-PERIODIC/periodic_check",
        headers={"Authorization": f"Bearer {agent_token}"},
        files={"photo": ("test.jpg", fake_img, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert "filename" in response.json()
    
    # Check Audit Log
    log = db_session.scalar(
        select(AuditLog).where(
            AuditLog.actor == "PC-12345-PERIODIC",
            AuditLog.action == "periodic_check_received"
        )
    )
    assert log is not None
