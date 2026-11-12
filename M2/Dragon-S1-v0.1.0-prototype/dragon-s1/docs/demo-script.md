# 5–7 Minute Demo Script

## 1. Introduction — 30 seconds

“Dragon S1 is a centralized USB access approval prototype for organization-owned Windows devices. It provides visible monitoring, identity evidence, real-time administrator approval and a complete audit trail.”

## 2. Architecture — 45 seconds

Show the diagram in `docs/architecture.md`: Windows agent, FastAPI server, WebSocket channel, database, compressed image storage and admin dashboard.

## 3. Live workflow — 3 minutes

1. Show the agent monitoring notice.
2. Click **Simulate USB insertion** or insert a real USB device.
3. Show automatic camera capture.
4. Choose an ID image, enter employee name and business reason.
5. Submit.
6. Switch to the dashboard; point out the instant notification, two images, face engine and score.
7. Approve the request.
8. Switch back to the agent and show the instant decision.
9. Explain that hardware Registry control is disabled in the demo for safety but implemented behind an explicit flag.

## 4. Management features — 1 minute

Show device online status, policy selector, user management, audit logs and overview counters.

## 5. Limitations and roadmap — 45 seconds

State clearly: TLS and device certificates, service/UI split, production biometric validation, encrypted storage, RBAC, rate limiting, HA and independent security testing are post-prototype work.
