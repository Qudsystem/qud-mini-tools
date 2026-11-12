from __future__ import annotations
import pytest
from unittest.mock import patch, MagicMock
from services.email import EmailService


def test_email_service_not_configured():
    svc = EmailService()
    # No SMTP configured
    result = svc.send_email(["test@example.com"], "Test", "<p>Hello</p>")
    # Should return False without crashing
    assert result == False


def test_email_service_configured():
    svc = EmailService()
    svc.host = "smtp.example.com"
    svc.port = 587
    svc.user = "user@example.com"
    svc.password = "password123"
    assert svc.is_configured() == True


def test_send_email_mocked():
    """Test that email gets sent when SMTP is mocked."""
    svc = EmailService()
    svc.host = "smtp.example.com"
    svc.port = 587
    svc.user = "user@example.com"
    svc.password = "password123"
    svc.from_addr = "user@example.com"
    
    with patch("services.email.smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
        
        result = svc.send_email(
            to=["recipient@example.com"],
            subject="Test",
            body_html="<p>Hello</p>",
            body_text="Hello"
        )
    # Should succeed with mocked SMTP
    assert result == True


def test_access_request_alert_not_configured():
    svc = EmailService()
    result = svc.send_access_request_alert(
        to=["admin@example.com"],
        employee_name="Ahmed",
        device_uid="PC-001",
        request_id=1,
        reason="USB needed",
    )
    assert result == False
