from __future__ import annotations

import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from database import get_db
from models import Notification, User
from rbac import require_permission

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    id: int
    channel: str
    severity: str
    title: str
    message: str
    data: dict
    is_read: bool
    is_sent: bool
    created_at: str


def notification_dict(n: Notification) -> dict:
    try:
        data_dict = json.loads(n.data) if n.data else {}
    except Exception:
        data_dict = {}
        
    return {
        "id": n.id,
        "channel": n.channel,
        "severity": n.severity,
        "title": n.title,
        "message": n.message,
        "data": data_dict,
        "is_read": n.is_read,
        "is_sent": n.is_sent,
        "created_at": n.created_at.isoformat()
    }


@router.get("", response_model=list[NotificationResponse])
def list_notifications(
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("notifications.view"))
):
    """List all notifications. Admins/Managers view all, others see theirs only."""
    query = select(Notification).order_by(Notification.created_at.desc()).limit(limit)
    if user.role not in {"admin", "manager"}:
        query = query.where(Notification.recipient_id == user.id)
        
    notifications = db.scalars(query).all()
    return [notification_dict(n) for n in notifications]


@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("notifications.view"))
):
    """Get the number of unread notifications."""
    query = select(func.count(Notification.id)).where(Notification.is_read == False)
    if user.role not in {"admin", "manager"}:
        query = query.where(Notification.recipient_id == user.id)
        
    count = db.scalar(query) or 0
    return {"unread_count": count}


@router.put("/{notification_id}/read")
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("notifications.view"))
):
    """Mark a notification as read."""
    n = db.get(Notification, notification_id)
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    # Check permission
    if user.role not in {"admin", "manager"} and n.recipient_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this notification")
        
    n.is_read = True
    n.read_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True}


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("notifications.manage"))
):
    """Delete a notification."""
    n = db.get(Notification, notification_id)
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    if user.role not in {"admin", "manager"} and n.recipient_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this notification")
        
    db.delete(n)
    db.commit()
    return {"ok": True}
