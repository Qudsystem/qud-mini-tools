from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_admin_ws_invalid_token(client: TestClient):
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/admin?token=invalid") as websocket:
            pass


def test_admin_ws_non_admin_role(client: TestClient, operator_token: str):
    # Operator token cannot connect to /ws/admin
    with pytest.raises(Exception):
        with client.websocket_connect(f"/ws/admin?token={operator_token}") as websocket:
            pass
            
            
def test_admin_ws_connect_success(client: TestClient, admin_token: str):
    # This should succeed since admin token is valid and role is admin
    with client.websocket_connect(f"/ws/admin?token={admin_token}") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "connected"
        assert data["role"] == "admin"
