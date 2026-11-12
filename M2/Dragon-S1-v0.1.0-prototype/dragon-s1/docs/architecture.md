# Architecture

```mermaid
flowchart LR
    U[Employee] --> A[Windows Agent / PyQt5]
    USB[USB Insert Event / WMI] --> A
    CAM[OpenCV Camera] --> A
    A -->|HTTPS multipart request| API[FastAPI Central Server]
    API --> DB[(SQLite or PostgreSQL)]
    API --> FS[(Compressed WebP Storage)]
    API --> FM[DeepFace or labeled demo fallback]
    API -->|WebSocket event| D[Admin Dashboard]
    D -->|Approve / Reject| API
    API -->|WebSocket decision| A
    A --> POLICY[Logical policy or optional USBSTOR Registry control]
```

## Trust boundaries

1. Agent enrollment uses a shared prototype enrollment key.
2. After enrollment, the agent receives a scoped JWT.
3. Admins authenticate with username and password and receive an admin JWT.
4. Images are compressed to WebP and retained for 15 days by default.
5. The dashboard is served from the same FastAPI origin to simplify deployment.

## Why no Windows Service for the modal

Windows services run in Session 0. Interactive UI shown from a service is unsupported and unsafe. The delivered agent runs in the signed-in user's desktop and can be installed as a highest-privilege scheduled task at logon. A future production design can separate a privileged headless service from an unprivileged UI process using authenticated local IPC.
