# Setup Guide

## Supported prototype environment

- Server: Windows 10/11, Linux or macOS; Python 3.10 recommended
- Agent: Windows 8/8.1/10/11. Use Python 3.10 on Windows 8.1+; use the legacy Python 3.8 runtime only when demonstrating on Windows 8.0.
- Windows 8.0 and Python 3.8 are end-of-life and should not be used for production deployment.
- Two machines on the same LAN are recommended for the final demonstration.

## Server setup

1. Copy `.env.example` to `.env`.
2. Replace `DRAGON_SECRET_KEY`, admin password and enrollment key.
3. Run `run_server.bat`.
4. Allow TCP port 8000 through Windows Firewall on a private network.
5. Open `http://SERVER_IP:8000`.

SQLite is the default and requires no Docker. For PostgreSQL:

```text
DRAGON_DATABASE_URL=postgresql+psycopg2://dragon_admin:PASSWORD@127.0.0.1:5432/dragon_s1
```

Then run `docker compose up -d` before starting the server.

## Agent setup

1. Copy the project to the endpoint.
2. In `.env`, set `DRAGON_SERVER_URL=http://SERVER_IP:8000`.
3. Keep `DRAGON_AGENT_DEMO_MODE=true` during the presentation.
4. Run `run_agent.bat`.
5. Approve Windows camera permission when prompted.

For real WMI event detection, `pywin32` and `WMI` are installed automatically on Windows.

## Optional hardware control

Set `DRAGON_HARDWARE_USB_CONTROL=true` and launch the agent as Administrator. The implementation changes `HKLM\\SYSTEM\\CurrentControlSet\\Services\\USBSTOR\\Start` between 3 and 4. This is system-wide, may require device reconnection, and should only be tested on a lab endpoint.

## Logon startup

Run PowerShell as Administrator:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_agent_task.ps1
```

## Tests

```bat
cd server
.venv\Scripts\activate
pip install pytest httpx
cd ..
pytest -q
```
