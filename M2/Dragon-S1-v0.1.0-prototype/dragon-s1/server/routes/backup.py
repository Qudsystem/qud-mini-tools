from __future__ import annotations

import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import BackupRecord, User
from rbac import require_permission
from services.backup import BackupService, BACKUPS_DIR

router = APIRouter(prefix="/api/backup", tags=["backup"])


class BackupIn(BaseModel):
    backup_type: str = "full" # full, differential


@router.get("", response_model=list)
def list_backups(
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission("*")),
):
    records = db.scalars(select(BackupRecord).order_by(BackupRecord.created_at.desc())).all()
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "backup_type": r.backup_type,
            "size_bytes": r.size_bytes,
            "checksum": r.checksum,
            "is_verified": r.is_verified,
            "verified_at": r.verified_at.isoformat() if r.verified_at else None,
            "created_at": r.created_at.isoformat(),
            "created_by": r.created_by
        }
        for r in records
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_backup(
    data: BackupIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission("*")),
):
    svc = BackupService(db)
    try:
        record = svc.create_backup(backup_type=data.backup_type, created_by=admin.username)
        return {"id": record.id, "filename": record.filename, "ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create backup: {str(e)}")


@router.post("/{backup_id}/verify")
def verify_backup(
    backup_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission("*")),
):
    svc = BackupService(db)
    is_valid = svc.verify_backup(backup_id)
    if is_valid:
        return {"id": backup_id, "status": "valid", "message": "Backup verified successfully."}
    else:
        raise HTTPException(status_code=400, detail="Backup verification failed or file missing.")


@router.post("/{backup_id}/restore")
def restore_backup(
    backup_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission("*")),
):
    svc = BackupService(db)
    try:
        success = svc.restore_backup(backup_id)
        if success:
            return {"id": backup_id, "ok": True, "message": "Database restored successfully."}
        else:
            raise HTTPException(status_code=400, detail="Restore operation failed.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restore database: {str(e)}")


@router.delete("/{backup_id}")
def delete_backup(
    backup_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission("*")),
):
    record = db.scalar(select(BackupRecord).where(BackupRecord.id == backup_id))
    if not record:
        raise HTTPException(status_code=404, detail="Backup record not found.")

    # Delete physical file
    backup_file_path = BACKUPS_DIR / record.filename
    if backup_file_path.exists():
        try:
            backup_file_path.unlink()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete backup file: {str(e)}")

    db.delete(record)
    db.commit()
    return {"id": backup_id, "ok": True, "message": "Backup record deleted successfully."}
