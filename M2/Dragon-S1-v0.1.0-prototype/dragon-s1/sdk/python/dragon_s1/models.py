from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict

class DeviceResponse(BaseModel):
    id: int
    device_uid: str
    hostname: str
    os_version: str
    agent_version: str
    is_enabled: bool
    usb_policy: str
    fail_secure: bool
    is_online: bool
    registered_at: str
    last_seen: str
    online: bool
    model_config = ConfigDict(extra="allow")

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str
    system: Dict[str, Any]
    uptime: str
    face_mode: str
    model_config = ConfigDict(extra="allow")
