from __future__ import annotations

import json
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import WebhookSubscription, User
from rbac import require_permission

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


class SubscribeIn(BaseModel):
    url: str
    secret_token: str = ""
    events: list[str] = ["*"] # default subscribe to all events


@router.get("", response_model=list)
def list_subscriptions(
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission("notifications.manage")),
):
    subs = db.scalars(select(WebhookSubscription)).all()
    return [
        {
            "id": s.id,
            "url": s.url,
            "events": json.loads(s.events),
            "is_active": s.is_active,
            "created_at": s.created_at.isoformat()
        }
        for s in subs
    ]


@router.post("/subscribe", status_code=status.HTTP_201_CREATED)
def subscribe(
    data: SubscribeIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission("notifications.manage")),
):
    # Check if already subscribed
    existing = db.scalar(select(WebhookSubscription).where(WebhookSubscription.url == data.url))
    if existing:
        existing.secret_token = data.secret_token
        existing.events = json.dumps(data.events)
        existing.is_active = True
        db.commit()
        return {"id": existing.id, "ok": True, "message": "Subscription updated."}

    sub = WebhookSubscription(
        url=data.url,
        secret_token=data.secret_token,
        events=json.dumps(data.events),
        is_active=True
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return {"id": sub.id, "ok": True, "message": "Subscribed successfully."}


@router.delete("/{sub_id}")
def unsubscribe(
    sub_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission("notifications.manage")),
):
    sub = db.scalar(select(WebhookSubscription).where(WebhookSubscription.id == sub_id))
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found.")

    db.delete(sub)
    db.commit()
    return {"id": sub_id, "ok": True, "message": "Unsubscribed successfully."}
