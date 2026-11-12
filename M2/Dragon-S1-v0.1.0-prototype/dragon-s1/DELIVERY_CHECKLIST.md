# Dragon S1 Delivery Checklist

## Included and tested

- [x] FastAPI server starts and creates the database
- [x] Default administrator is seeded from environment variables
- [x] JWT admin login
- [x] Device enrollment and heartbeat
- [x] Multipart access request with two images
- [x] WebP compression and image quality metrics
- [x] DeepFace integration path plus labeled demo fallback
- [x] Admin dashboard with live WebSocket events
- [x] Approve/reject decision returned to the agent
- [x] Device policies, user management, audit logs and statistics
- [x] Real-time events display with Arabic translations and WebSocket broadcasting
- [x] WMI USB monitor on Windows
- [x] Optional USBSTOR Registry control behind an explicit safety flag
- [x] 15-day retention worker and manual cleanup endpoint
- [x] Scheduled Task installer for interactive logon startup
- [x] API smoke test covering the complete workflow
- [x] Setup, architecture, API, demo and security documentation

## Before presentation

- [x] Copy `.env.example` to `.env`
- [x] Set the server LAN IP in `DRAGON_SERVER_URL` on the agent (set to 192.168.1.13:8000)
- [x] Start server and agent (server running on port 8000, agent registered successfully)
- [ ] Test camera and Windows Firewall port 8000 (camera has tamper detection issues, may need physical camera)
- [x] Keep hardware USB control disabled for the first demo (DRAGON_HARDWARE_USB_CONTROL=false)
- [ ] Change the default admin password after the presentation
