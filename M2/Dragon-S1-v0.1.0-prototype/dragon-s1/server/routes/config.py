from __future__ import annotations

import os
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Response, status
from pydantic import BaseModel
import yaml
import json

from config import settings
from models import User
from rbac import require_permission
from services.config_manager import ConfigManager, ConfigValidationError

router = APIRouter(prefix="/api/config", tags=["config"])
CONFIG_FILE_PATH = "dragon_config.yaml"


class ConfigValidateIn(BaseModel):
    config: dict


class ConfigUpdateIn(BaseModel):
    config: dict


@router.get("")
def get_config(
    admin: User = Depends(require_permission("*")),
):
    """Loads configuration and returns it (secrets are masked/excluded in UI if needed, returns full schema for admin)."""
    mgr = ConfigManager()
    cfg = mgr.load_config(CONFIG_FILE_PATH)
    return cfg


@router.put("")
def update_config(
    data: ConfigUpdateIn,
    admin: User = Depends(require_permission("*")),
):
    """Validates and saves new configuration settings."""
    mgr = ConfigManager()
    try:
        mgr.save_config(data.config, CONFIG_FILE_PATH)
        return {"ok": True, "message": "Configuration updated successfully."}
    except ConfigValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {str(e)}")


@router.post("/validate")
def validate_config(
    data: ConfigValidateIn,
    admin: User = Depends(require_permission("*")),
):
    """Checks validity of a configuration dictionary against the system schemas."""
    mgr = ConfigManager()
    valid, errors = mgr.validate_config(data.config)
    return {"valid": valid, "errors": errors}


@router.get("/export")
def export_config(
    format: str = Query("yaml", description="Format to export: yaml or json"),
    admin: User = Depends(require_permission("*")),
):
    """Export current configuration as a downloadable file."""
    mgr = ConfigManager()
    cfg = mgr.load_config(CONFIG_FILE_PATH)
    
    fmt = format.lower().strip()
    if fmt == "json":
        content = json.dumps(cfg, indent=4)
        media_type = "application/json"
        filename = "dragon_config.json"
    else:
        content = yaml.safe_dump(cfg, default_flow_style=False, sort_keys=False)
        media_type = "application/x-yaml"
        filename = "dragon_config.yaml"
        
    return Response(
        content=content.encode("utf-8"),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/import")
async def import_config(
    file: UploadFile = File(...),
    admin: User = Depends(require_permission("*")),
):
    """Uploads and registers a new configuration file."""
    content = await file.read()
    file_str = content.decode("utf-8")
    
    file_ext = os.path.splitext(file.filename or "")[1].lower()
    
    try:
        if file_ext in {".yaml", ".yml"}:
            cfg_dict = yaml.safe_load(file_str) or {}
        elif file_ext == ".json":
            cfg_dict = json.loads(file_str) or {}
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Use YAML or JSON.")
            
        mgr = ConfigManager()
        mgr.save_config(cfg_dict, CONFIG_FILE_PATH)
        return {"ok": True, "message": "Configuration imported and saved successfully."}
    except ConfigValidationError as e:
        raise HTTPException(status_code=400, detail=f"Import validation failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")
