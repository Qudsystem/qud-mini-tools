from __future__ import annotations

import io
import pytest
import httpx
from PIL import Image

from main import app
from models import User
from sdk.dragon_sdk import DragonClient, DragonSDKError


def test_sdk_integration(client: TestClient, db_session: Session, test_admin: User):
    # Instantiate client and mock local HTTP layer using TestClient
    sdk_client = DragonClient("http://testserver")
    sdk_client._client = client

    # 1. Health check
    health = sdk_client.get_health()
    assert health["service"] == "Dragon S1"
    assert health["status"] == "ok"

    # 2. Login
    token = sdk_client.login("testadmin", "adminpass123")
    assert token != ""
    assert sdk_client.token == token

    # 3. Register device
    reg = sdk_client.register_device(
        device_uid="PC-SDK-TEST",
        hostname="sdk-host",
        os_version="Windows 11",
        enrollment_key="dragon-enroll-2026"
    )
    assert reg["device"]["device_uid"] == "PC-SDK-TEST"
    agent_token = reg["agent_token"]
    
    # 4. Create request (requires agent client token)
    agent_client = DragonClient("http://testserver", token=agent_token)
    agent_client._client = client
    
    # Create valid JPEG bytes
    img = Image.new("RGB", (100, 100), color="blue")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_bytes = img_byte_arr.getvalue()
    
    face_path = "tests/temp_face.jpg"
    id_path = "tests/temp_id.jpg"
    with open(face_path, "wb") as f1, open(id_path, "wb") as f2:
        f1.write(img_bytes)
        f2.write(img_bytes)
        
    try:
        req = agent_client.create_request(
            device_uid="PC-SDK-TEST",
            employee_name="Alice Dev",
            reason="SDK testing",
            usb_description="SanDisk Cruiser",
            face_image_path=face_path,
            id_image_path=id_path
        )
        assert req["employee_name"] == "Alice Dev"
    finally:
        import os
        if os.path.exists(face_path): os.remove(face_path)
        if os.path.exists(id_path): os.remove(id_path)
