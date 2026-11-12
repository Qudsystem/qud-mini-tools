from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session
import csv
import json
import io

from database import get_db
from models import AuditLog, User
from rbac import require_permission
from services.audit import AuditService
from utils.pagination import paginate

router = APIRouter(prefix="/api/compliance", tags=["compliance"])


@router.get("/verify")
def verify_audit_trail(
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission("audit.view")),
):
    """Verifies the integrity of the audit logs chain. Returns list of corrupted records if any."""
    svc = AuditService(db)
    is_secure, corrupted = svc.verify_chain()
    return {
        "integrity_verified": is_secure,
        "status": "secure" if is_secure else "compromised",
        "corrupted_records_count": len(corrupted),
        "corrupted_ids": corrupted
    }


@router.get("/logs")
def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission("audit.view")),
):
    """Retrieve audit logs with pagination and verify verification metrics."""
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
    res = paginate(
        db=db,
        statement=stmt,
        page=page,
        page_size=page_size,
        dict_converter=lambda log: {
            "id": log.id,
            "actor": log.actor,
            "action": log.action,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "details": log.details,
            "signature": log.signature,
            "previous_hash": log.previous_hash,
            "created_at": log.created_at.isoformat()
        }
    )
    return res


@router.get("/export")
def export_compliance_logs(
    format: str = Query("json", description="Format to export: json or csv"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission("audit.view")),
):
    """Export compliance audit logs for external auditors."""
    logs = db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc())).all()
    
    fmt = format.lower().strip()
    if fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Actor", "Action", "Target Type", "Target ID", "Details", "Signature", "Previous Hash", "Created At"])
        for l in logs:
            writer.writerow([
                l.id, l.actor, l.action, l.target_type, l.target_id,
                l.details, l.signature, l.previous_hash, l.created_at.isoformat()
            ])
        return Response(
            content=output.getvalue().encode("utf-8"),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=compliance_audit_logs.csv"}
        )
    else:
        log_list = [
            {
                "id": l.id,
                "actor": l.actor,
                "action": l.action,
                "target_type": l.target_type,
                "target_id": l.target_id,
                "details": l.details,
                "signature": l.signature,
                "previous_hash": l.previous_hash,
                "created_at": l.created_at.isoformat()
            }
            for l in logs
        ]
        return Response(
            content=json.dumps(log_list, indent=4).encode("utf-8"),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=compliance_audit_logs.json"}
        )
