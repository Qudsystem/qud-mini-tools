from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models import Device, AccessRequest, Session as DBSessionModel


@pytest.fixture(name="active_session")
def fixture_active_session(db_session: Session) -> DBSessionModel:
    device = Device(device_uid="PC-SESS-DEV", hostname="sess-host", is_online=True)
    req = AccessRequest(
        device_id=1,
        device_uid="PC-SESS-DEV",
        employee_name="John Doe",
        reason="some reason",
        face_image_path="face.jpg",
        id_image_path="id.jpg"
    )
    db_session.add_all([device, req])
    db_session.flush()

    session_obj = DBSessionModel(
        device_id=device.id,
        device_uid=device.device_uid,
        request_id=req.id,
        employee_name="John Doe",
        status="active"
    )
    db_session.add(session_obj)
    db_session.commit()
    db_session.refresh(session_obj)
    return session_obj


def test_list_sessions(client: TestClient, active_session: DBSessionModel, admin_headers: dict):
    response = client.get("/api/sessions", headers=admin_headers)
    assert response.status_code == 200
    sessions = response.json()
    assert len(sessions) > 0
    assert sessions[0]["device_uid"] == "PC-SESS-DEV"
    assert sessions[0]["status"] == "active"


def test_revoke_session(client: TestClient, active_session: DBSessionModel, admin_headers: dict):
    response = client.post(f"/api/sessions/{active_session.id}/revoke", json={"reason": "Testing revocation"}, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "revoked"
    assert response.json()["revoked_by"] == "testadmin"

