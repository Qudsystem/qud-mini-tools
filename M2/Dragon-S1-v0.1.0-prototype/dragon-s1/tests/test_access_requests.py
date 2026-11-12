from __future__ import annotations

import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models import Device, AccessRequest


@pytest.fixture(name="enrolled_device")
def fixture_enrolled_device(db_session: Session) -> Device:
    device = Device(device_uid="PC-REQ-DEV", hostname="req-host", is_online=True)
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device


from PIL import Image

def test_create_request_success(client: TestClient, enrolled_device: Device, agent_headers: dict):
    # Create valid JPEG bytes
    img = Image.new("RGB", (100, 100), color="red")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    valid_image_bytes = img_byte_arr.getvalue()

    data = {
        "device_uid": "PC-REQ-DEV",
        "employee_name": "John Doe",
        "reason": "Need to copy log files for debugging",
        "usb_description": "Kingston DataTraveler"
    }
    
    # Create fake files
    face_file = ("face.jpg", io.BytesIO(valid_image_bytes), "image/jpeg")
    id_file = ("id.jpg", io.BytesIO(valid_image_bytes), "image/jpeg")
    
    files = {
        "face_image": face_file,
        "id_image": id_file
    }


    # Enrollment/Agent requests require agent headers
    response = client.post("/api/requests", data=data, files=files, headers=agent_headers)

    assert response.status_code == 200
    json_data = response.json()
    assert json_data["employee_name"] == "John Doe"
    assert json_data["device_uid"] == "PC-REQ-DEV"
    assert json_data["status"] == "pending"


def test_approve_request(client: TestClient, db_session: Session, enrolled_device: Device, admin_headers: dict):
    req = AccessRequest(
        device_id=enrolled_device.id,
        device_uid=enrolled_device.device_uid,
        employee_name="Alice Smith",
        reason="Work task",
        face_image_path="test_face.webp",
        id_image_path="test_id.webp",
        status="pending"
    )
    db_session.add(req)
    db_session.commit()
    db_session.refresh(req)

    payload = {"decision": "approved", "note": "Approved by supervisor"}
    response = client.post(f"/api/requests/{req.id}/decision", json=payload, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert response.json()["decided_by"] == "testadmin"


def test_reject_request(client: TestClient, db_session: Session, enrolled_device: Device, admin_headers: dict):
    req = AccessRequest(
        device_id=enrolled_device.id,
        device_uid=enrolled_device.device_uid,
        employee_name="Bob Smith",
        reason="Work task",
        face_image_path="test_face.webp",
        id_image_path="test_id.webp",
        status="pending"
    )
    db_session.add(req)
    db_session.commit()
    db_session.refresh(req)

    payload = {"decision": "rejected", "note": "Unauthorized action"}
    response = client.post(f"/api/requests/{req.id}/decision", json=payload, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
