from __future__ import annotations

import os
import secrets
import logging
import warnings
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

logger = logging.getLogger("dragon.config")

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_DIR / ".env")
except Exception:
    pass


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    secret_key: str = os.getenv("DRAGON_SECRET_KEY", "")
    database_url: str = os.getenv("DRAGON_DATABASE_URL", "postgresql://dragon_admin:DragonS1_Secure_2026@localhost:5432/dragon_s1")
    admin_username: str = os.getenv("DRAGON_ADMIN_USERNAME", "admin")
    admin_password: str = os.getenv("DRAGON_ADMIN_PASSWORD", "")
    enrollment_key: str = os.getenv("DRAGON_ENROLLMENT_KEY", "dragon-enroll-2026")
    token_expire_minutes: int = int(os.getenv("DRAGON_TOKEN_EXPIRE_MINUTES", "480"))
    face_match_mode: str = os.getenv("DRAGON_FACE_MATCH_MODE", "auto").lower()
    retention_days: int = int(os.getenv("DRAGON_UPLOAD_RETENTION_DAYS", "15"))
    max_upload_mb: int = int(os.getenv("DRAGON_MAX_UPLOAD_MB", "8"))
    uploads_dir: Path = BASE_DIR / "uploads"
    dashboard_dir: Path = PROJECT_DIR / "dashboard"
    cors_origins: str = os.getenv("DRAGON_CORS_ORIGINS", "*")
    debug: bool = _bool("DRAGON_DEBUG", False)
    
    # Advanced production configuration settings
    rate_limit_per_minute: int = int(os.getenv("DRAGON_RATE_LIMIT_PER_MINUTE", "100"))
    max_login_attempts: int = int(os.getenv("DRAGON_MAX_LOGIN_ATTEMPTS", "5"))
    smtp_host: str = os.getenv("DRAGON_SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("DRAGON_SMTP_PORT", "587"))
    smtp_user: str = os.getenv("DRAGON_SMTP_USER", "")
    smtp_password: str = os.getenv("DRAGON_SMTP_PASSWORD", "")


# Instantiate and validate settings
settings = Settings()
settings.uploads_dir.mkdir(parents=True, exist_ok=True)

# Post-instantiation settings validation
if not settings.secret_key:
    new_key = secrets.token_hex(32)
    object.__setattr__(settings, 'secret_key', new_key)
    print(f"[*] Generated new DRAGON_SECRET_KEY: {new_key}")

if not settings.admin_password:
    new_pass = secrets.token_urlsafe(16)
    object.__setattr__(settings, 'admin_password', new_pass)
    print(f"[*] Generated new DRAGON_ADMIN_PASSWORD: {new_pass}")

