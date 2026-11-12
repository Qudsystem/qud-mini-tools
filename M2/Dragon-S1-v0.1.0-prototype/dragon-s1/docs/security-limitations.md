# Security, Privacy and Prototype Limitations

Dragon S1 must be used only on organization-owned or explicitly authorized devices with visible notice and a documented privacy basis.

## Prototype limitations

- HTTP is used by default; production requires TLS.
- Device enrollment uses a shared key; production requires unique device certificates or signed provisioning tokens.
- Uploaded images are available from unpredictable URLs but are not independently authorized; production requires authenticated object access.
- The dashboard has one administrator role; production requires least-privilege RBAC.
- DeepFace is optional and its output must not be the sole basis for an employment or access decision.
- Demo image similarity is not biometric identification.
- USBSTOR Registry control is system-wide and is not equivalent to kernel-level DLP enforcement.
- No anti-tamper driver, offline queue, high availability, SIEM integration or certificate rotation is included.

## Required production controls

TLS, encrypted storage, secrets management, signed updates, per-device credentials, RBAC, data minimization, configurable retention, consent/notice records, incident response, legal review, accessibility testing, audit export, monitoring and penetration testing.
