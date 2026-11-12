from __future__ import annotations

from fastapi.testclient import TestClient
from security import hash_password, verify_password, create_token, decode_token
from rbac import has_permission, Role


def test_password_hashing():
    pw = "SecretSecurePass123!"
    h = hash_password(pw)
    assert h != pw
    assert verify_password(pw, h) is True
    assert verify_password("wrong", h) is False


def test_token_creation_and_decode():
    token = create_token("testuser", "operator")
    decoded = decode_token(token)
    assert decoded["sub"] == "testuser"
    assert decoded["role"] == "operator"



def test_rbac_permission_matrix():
    assert has_permission("admin", "any.permission") is True
    assert has_permission("manager", "devices.view") is True
    assert has_permission("manager", "devices.manage") is True
    assert has_permission("operator", "devices.view") is True
    assert has_permission("operator", "devices.manage") is False
    assert has_permission("viewer", "devices.view") is True
    assert has_permission("viewer", "requests.decide") is False
    assert has_permission("invalid_role", "devices.view") is False


def test_security_headers_present(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    headers = response.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("Strict-Transport-Security") == "max-age=31536000; includeSubDomains"
    assert "default-src 'self'" in headers.get("Content-Security-Policy", "")
