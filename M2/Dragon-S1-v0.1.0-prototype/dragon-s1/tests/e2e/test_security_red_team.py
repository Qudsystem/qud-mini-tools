import httpx
import pytest
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://127.0.0.1:3001"

def fetch_health(_):
    try:
        with httpx.Client() as client:
            return client.get(f"{BASE_URL}/api/health", timeout=2)
    except Exception as e:
        return e

def test_ddos_rate_limit():
    # Send 150 requests quickly using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(fetch_health, range(150)))
    
    status_codes = [r.status_code for r in results if hasattr(r, 'status_code')]
    assert 429 in status_codes, "Rate limiter did not block the DDoS attack!"

def test_csrf_bypass_attempt():
    # Try to call a protected endpoint without CSRF token
    with httpx.Client() as client:
        response = client.post(f"{BASE_URL}/api/auth/login", json={"username": "testadmin", "password": "adminpass123"})
        assert response.status_code in [403, 400], "CSRF protection bypassed or missing!"

def test_privilege_escalation():
    # Attempt to access admin routes without a valid token
    with httpx.Client() as client:
        response = client.get(f"{BASE_URL}/api/admin/metrics")
        assert response.status_code == 401, "Admin endpoint accessible without auth!"


