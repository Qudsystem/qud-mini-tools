import os
from pathlib import Path

os.environ["DRAGON_DATABASE_URL"] = "sqlite:///./test_dragon_s1.db"
os.environ["DRAGON_FACE_MATCH_MODE"] = "demo"
os.environ["DRAGON_ADMIN_USERNAME"] = "admin"
os.environ["DRAGON_ADMIN_PASSWORD"] = "DragonS1@2026"
os.environ["DRAGON_SECRET_KEY"] = "test-secret-key-that-is-longer-than-32-bytes"

from fastapi.testclient import TestClient
from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
from main import app


def make_image(path: Path, shade: int):
    Image.new("RGB", (320, 240), (shade, shade, shade)).save(path)


def test_full_workflow(tmp_path):
    with TestClient(app) as client:
        response = client.get("/api/health")
        csrf_token = client.cookies.get("csrftoken")
        if csrf_token:
            client.headers.update({"x-csrftoken": csrf_token})
            
        login = client.post("/api/auth/login", json={"username": "admin", "password": "DragonS1@2026"})
        assert login.status_code == 200
        admin = {"Authorization": f"Bearer {login.json()['access_token']}"}
        assert client.get("/").status_code == 200
        reg = client.post("/api/devices/register", json={"device_uid":"TEST-01","hostname":"TEST-PC","os_version":"Windows Test","agent_version":"0.1.0","enrollment_key":"dragon-enroll-2026"})
        assert reg.status_code == 200
        agent = {"Authorization": f"Bearer {reg.json()['agent_token']}"}
        face = tmp_path / "face.png"; card = tmp_path / "id.png"
        make_image(face, 120); make_image(card, 125)
        with face.open("rb") as f1, card.open("rb") as f2:
            created = client.post("/api/requests", headers=agent, data={"device_uid":"TEST-01","employee_name":"Test Employee","reason":"Test transfer","usb_description":"Test USB"}, files={"face_image":("face.png",f1,"image/png"),"id_image":("id.png",f2,"image/png")})
        assert created.status_code == 200
        request_id = created.json()["id"]
        decision = client.post(f"/api/requests/{request_id}/decision", headers=admin, json={"decision":"approved","note":"Test approved"})
        assert decision.status_code == 200
        assert decision.json()["status"] == "approved"
        assert client.get("/api/devices", headers=admin).json()[0]["online"] is True
        assert client.get("/api/admin/stats", headers=admin).json()["approved_requests"] >= 1
