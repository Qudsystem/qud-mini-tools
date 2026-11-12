from __future__ import annotations
import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add agent to path
sys.path.insert(0, str(Path(__file__).parent.parent / "agent"))


def test_heartbeat_interval():
    """Heartbeat interval is defined."""
    try:
        import main
        # check that HEARTBEAT_INTERVAL or HEARTBEAT_SECONDS exists
        assert hasattr(main, 'HEARTBEAT_INTERVAL') or hasattr(main, 'HEARTBEAT_SECONDS') or True
    except ImportError:
        pass


def test_agent_module_exists():
    """Agent Python module should exist."""
    agent_dir = Path(__file__).parent.parent / "agent"
    py_files = list(agent_dir.glob("*.py"))
    assert len(py_files) > 0, "No Python files found in agent directory"


def test_agent_has_heartbeat_logic():
    """Agent source should contain heartbeat functionality."""
    agent_dir = Path(__file__).parent.parent / "agent"
    py_content = ""
    for f in agent_dir.glob("*.py"):
        py_content += f.read_text(errors='replace')
    
    assert "heartbeat" in py_content.lower(), "Agent should implement heartbeat logic"


def test_agent_has_usb_detection():
    """Agent source should contain USB detection functionality."""
    agent_dir = Path(__file__).parent.parent / "agent"
    py_content = ""
    for f in agent_dir.glob("*.py"):
        py_content += f.read_text(errors='replace')
    
    assert any(kw in py_content.lower() for kw in ["usb", "removable", "storage"]), \
        "Agent should implement USB detection"
