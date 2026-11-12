"""Reserved for a future headless service.

The interactive Dragon S1 agent is intentionally not installed as a Windows Service because
Session 0 services cannot display a PyQt permission dialog in the signed-in user's desktop.
Use scripts/install_agent_task.ps1 to launch the interactive agent at user logon.
"""

if __name__ == "__main__":
    raise SystemExit("Use the scheduled-task installer for the interactive agent. See README.md.")
