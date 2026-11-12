from __future__ import annotations

CONFIG_SCHEMA = {
    "server": {
        "host": {"type": "str", "default": "0.0.0.0"},
        "port": {"type": "int", "range": [1, 65535], "default": 8000},
        "debug": {"type": "bool", "default": False},
        "workers": {"type": "int", "range": [1, 32], "default": 4},
    },
    "security": {
        "token_expire_minutes": {"type": "int", "range": [5, 1440], "default": 480},
        "max_login_attempts": {"type": "int", "range": [3, 20], "default": 5},
        "rate_limit_per_minute": {"type": "int", "range": [10, 1000], "default": 100},
    },
    "storage": {
        "uploads_dir": {"type": "str", "required": True},
        "max_upload_mb": {"type": "int", "range": [1, 100], "default": 8},
        "retention_days": {"type": "int", "range": [1, 365], "default": 15},
    },
    "face_recognition": {
        "mode": {"type": "str", "choices": ["auto", "deepface", "demo"], "default": "auto"},
        "threshold": {"type": "float", "range": [0.0, 1.0], "default": 0.6},
    },
}
