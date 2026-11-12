from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="http://127.0.0.1:8000")
    parser.add_argument("--enrollment-key", default="dragon-enroll-2026")
    parser.add_argument("--face", default=str(Path(__file__).parent / "demo_face.png"))
    parser.add_argument("--id", dest="id_image", default=str(Path(__file__).parent / "demo_id.png"))
    args = parser.parse_args()
    device_uid = "DEMO-ENDPOINT-01"
    reg = requests.post(f"{args.server}/api/devices/register", json={"device_uid":device_uid,"hostname":"DEMO-PC","os_version":"Windows 11 Demo","agent_version":"0.1.0","enrollment_key":args.enrollment_key}, timeout=10)
    reg.raise_for_status(); token=reg.json()["agent_token"]
    with open(args.face,"rb") as face, open(args.id_image,"rb") as card:
        result=requests.post(f"{args.server}/api/requests",headers={"Authorization":f"Bearer {token}"},data={"device_uid":device_uid,"employee_name":"Demo Employee","reason":"Transfer approved presentation files","usb_description":"SanDisk Demo USB"},files={"face_image":("face.png",face,"image/png"),"id_image":("id.png",card,"image/png")},timeout=120)
    result.raise_for_status(); print(json.dumps(result.json(),indent=2))

if __name__=="__main__": main()
