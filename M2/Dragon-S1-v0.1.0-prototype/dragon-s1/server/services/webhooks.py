from __future__ import annotations

import hmac
import hashlib
import json
import logging
import httpx
from datetime import datetime, timezone
from sqlalchemy import select
from database import SessionLocal
from models import WebhookSubscription

logger = logging.getLogger("dragon.webhooks")


async def dispatch_webhook(event_type: str, payload: dict) -> None:
    """Dispatches a webhook event to all active subscribers in the background."""
    try:
        with SessionLocal() as db:
            subs = db.scalars(
                select(WebhookSubscription).where(WebhookSubscription.is_active == True)
            ).all()
            
            matching_subs = []
            for s in subs:
                try:
                    events_list = json.loads(s.events)
                except Exception:
                    events_list = []
                if "*" in events_list or event_type in events_list:
                    matching_subs.append(s)
                    
            if not matching_subs:
                return

            event_data = {
                "event": event_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": payload
            }
            body = json.dumps(event_data)
            body_bytes = body.encode("utf-8")

            async with httpx.AsyncClient(timeout=10.0) as client:
                for sub in matching_subs:
                    headers = {"Content-Type": "application/json"}
                    
                    # Cryptographic signature
                    if sub.secret_token:
                        sig = hmac.new(
                            sub.secret_token.encode("utf-8"),
                            body_bytes,
                            hashlib.sha256
                        ).hexdigest()
                        headers["X-Dragon-Signature"] = sig

                    try:
                        logger.info("Sending webhook event '%s' to %s", event_type, sub.url)
                        response = await client.post(sub.url, content=body, headers=headers)
                        logger.info("Webhook to %s returned status: %d", sub.url, response.status_code)
                    except Exception as e:
                        logger.error("Failed to send webhook to %s: %s", sub.url, str(e))
    except Exception as exc:
        logger.error("Error in webhook dispatcher: %s", str(exc))
