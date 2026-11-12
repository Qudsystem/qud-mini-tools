import pytest
from fastapi.testclient import TestClient
from main import app

def test_csrf_missing():
    with TestClient(app) as client:
        # POST without fetching or sending CSRF token
        response = client.post("/api/auth/login", json={"username": "test", "password": "password"})
        assert response.status_code == 403
        assert "CSRF" in response.text

def test_csrf_provided():
    with TestClient(app) as client:
        # Fetch token
        client.get("/api/health")
        token = client.cookies.get("csrftoken")
        assert token is not None
        
        # Send POST with token
        client.headers.update({"x-csrftoken": token})
        response = client.post("/api/auth/login", json={"username": "test", "password": "password"})
        # Should not be 403 (could be 401 unauthorized, but not 403 CSRF error)
        assert response.status_code != 403
