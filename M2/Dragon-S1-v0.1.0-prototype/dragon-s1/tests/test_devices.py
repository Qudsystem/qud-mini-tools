from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models import Device


def test_enroll_device_success(client: TestClient):
    payload = {
        "device_uid": "PC-TEST-999",
        "hostname": "test-host",
        "os_version": "Windows 11 Pro",
        "agent_version": "0.1.0",
        "enrollment_key": "dragon-enroll-2026"
    }
    response = client.post("/api/devices/register", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert "agent_token" in json_data
    assert json_data["device"]["device_uid"] == "PC-TEST-999"


def test_enroll_device_rbac_denied(client: TestClient, operator_headers: dict):
    # Testing RBAC on set policy instead of enroll since enroll is public to agents
    response = client.patch("/api/devices/1/policy", json={"policy": "block"}, headers=operator_headers)
    assert response.status_code == 403


def test_enroll_duplicate_device(client: TestClient, db_session: Session):
    # Device registration is idempotent; it updates if duplicate rather than erroring out
    # So duplicate registration updates it and succeeds
    payload = {
        "device_uid": "PC-DUPLICATE",
        "hostname": "host-dup",
        "os_version": "Windows 11 Pro",
        "agent_version": "0.1.0",
        "enrollment_key": "dragon-enroll-2026"
    }
    response1 = client.post("/api/devices/register", json=payload)
    assert response1.status_code == 200
    
    # Registering again should succeed and return the device
    response2 = client.post("/api/devices/register", json=payload)
    assert response2.status_code == 200
    assert response2.json()["device"]["device_uid"] == "PC-DUPLICATE"


def test_list_devices(client: TestClient, db_session: Session, operator_headers: dict):
    device1 = Device(device_uid="PC-LIST-1", hostname="host-list1", is_online=True)
    device2 = Device(device_uid="PC-LIST-2", hostname="host-list2", is_online=False)
    db_session.add_all([device1, device2])
    db_session.commit()

    response = client.get("/api/devices", headers=operator_headers)
    assert response.status_code == 200
    devices = response.json()
    uids = [d["device_uid"] for d in devices]
    assert "PC-LIST-1" in uids
    assert "PC-LIST-2" in uids


def test_update_device_policy(client: TestClient, db_session: Session, admin_headers: dict):
    device = Device(device_uid="PC-POLICY", hostname="host-policy", usb_policy="block")
    db_session.add(device)
    db_session.commit()

    response = client.patch(f"/api/devices/{device.id}/policy", json={"policy": "approval"}, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["usb_policy"] == "approval"

