# Dragon S1 Python SDK

The official Python SDK for the Dragon S1 Central Security System.

## Installation

You can install the SDK locally or via pip if published:

```bash
pip install -e .
```

## Quick Start

```python
from dragon_s1 import DragonS1Client

# Initialize the client
client = DragonS1Client(base_url="http://localhost:3000")

# Check health
health = client.get_health()
print(f"Status: {health.status}")

# Authenticate (Admin)
token = client.login(username="admin", password="changeme123")

# List devices
devices = client.list_devices()
for d in devices:
    print(f"Device: {d.hostname} - Online: {d.is_online}")
```

## Features
- Authentication
- Device Registration & Health Checks
- Access Request Workflows with Biometrics (Face ID)
