from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models import AuditLog
from services.audit import AuditService


def test_audit_trail_immutable_signing(db_session: Session):
    # 1. Add audit log entries
    log1 = AuditLog(actor="admin", action="test_action_1", details="details 1")
    db_session.add(log1)
    db_session.commit()
    db_session.refresh(log1)
    
    assert log1.signature != ""
    assert log1.previous_hash == "GENESIS_HASH"
    
    log2 = AuditLog(actor="manager", action="test_action_2", details="details 2")
    db_session.add(log2)
    db_session.commit()
    db_session.refresh(log2)
    
    assert log2.signature != ""
    assert log2.previous_hash == log1.signature


def test_compliance_verify_endpoints(client: TestClient, admin_headers: dict, db_session: Session):
    # Clear any logs
    db_session.query(AuditLog).delete()
    db_session.commit()
    
    # 1. Add logs sequentially to form valid signature chain
    l1 = AuditLog(actor="admin", action="create_user")
    db_session.add(l1)
    db_session.commit()
    
    l2 = AuditLog(actor="operator", action="disable_usb")
    db_session.add(l2)
    db_session.commit()


    # 2. Check verify endpoint
    response = client.get("/api/compliance/verify", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["integrity_verified"] is True
    assert data["status"] == "secure"
    assert data["corrupted_records_count"] == 0

    # 3. Tamper with a log
    l1.action = "malicious_change"
    db_session.commit()
    
    response2 = client.get("/api/compliance/verify", headers=admin_headers)
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["integrity_verified"] is False
    assert data2["status"] == "compromised"
    assert l1.id in data2["corrupted_ids"]


def test_backup_disaster_recovery_workflow(client: TestClient, admin_headers: dict):
    # 1. Trigger backup creation
    response = client.post("/api/backup", json={"backup_type": "full"}, headers=admin_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["ok"] is True
    backup_id = data["id"]
    
    # 2. List backups
    list_resp = client.get("/api/backup", headers=admin_headers)
    assert list_resp.status_code == 200
    backups = list_resp.json()
    assert len(backups) > 0
    assert any(b["id"] == backup_id for b in backups)
    
    # 3. Verify backup
    verify_resp = client.post(f"/api/backup/{backup_id}/verify", headers=admin_headers)
    assert verify_resp.status_code == 200
    assert verify_resp.json()["status"] == "valid"

    # 4. Restore backup
    restore_resp = client.post(f"/api/backup/{backup_id}/restore", headers=admin_headers)
    assert restore_resp.status_code == 200
    assert restore_resp.json()["ok"] is True
    
    # 5. Clean up backup
    del_resp = client.delete(f"/api/backup/{backup_id}", headers=admin_headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["ok"] is True
