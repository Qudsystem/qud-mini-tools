# API Summary

Interactive OpenAPI documentation is available at `/docs`.

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| POST | `/api/auth/login` | Public | Admin login |
| POST | `/api/devices/register` | Enrollment key | Enroll or refresh a device |
| POST | `/api/devices/heartbeat` | Agent JWT | Update online status |
| GET | `/api/devices` | Admin JWT | List devices |
| PATCH | `/api/devices/{id}/policy` | Admin JWT | Set approval/allow/block policy |
| POST | `/api/requests` | Agent JWT | Submit multipart USB request |
| GET | `/api/requests` | Admin JWT | List requests |
| POST | `/api/requests/{id}/decision` | Admin JWT | Approve or reject |
| GET/POST | `/api/users` | Admin JWT | List/create admins |
| PATCH | `/api/users/{id}/blocked` | Admin JWT | Block/unblock admin |
| DELETE | `/api/users/{id}` | Admin JWT | Delete admin |
| GET | `/api/admin/stats` | Admin JWT | Dashboard counters |
| GET | `/api/admin/logs` | Admin JWT | Audit log |
| GET | `/api/admin/events/latest` | Admin JWT | Latest audit events with Arabic translations |
| POST | `/api/admin/cleanup` | Admin JWT | Run image retention cleanup |

## WebSockets

- Admin: `/ws/admin?token=ADMIN_JWT`
- Agent: `/ws/agent/{device_uid}?token=AGENT_JWT`

Events:

- `request_created`
- `request_updated`
- `event_created` - Broadcasts new audit log events in real-time with Arabic translations
- `request_decision`
