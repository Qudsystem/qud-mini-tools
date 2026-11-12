# Connecting Agents via WireGuard VPN

For highly secure, isolated communication between the Dragon S1 Server and the Agents, setting up a VPN using WireGuard is recommended. This avoids exposing the server directly to the public internet.

## Prerequisites
- A central server (or the Dragon S1 Server machine) accessible via a public IP or accessible within your enterprise network.
- WireGuard installed on the Server and all Agent machines.

## 1. Install WireGuard

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install wireguard
```

**Windows / macOS:**
Download and install the WireGuard client from the [official website](https://www.wireguard.com/install/).

## 2. Server Configuration

On the server, generate the keys:
```bash
wg genkey | tee server_private.key | wg pubkey > server_public.key
```

Create the configuration file `/etc/wireguard/wg0.conf`:
```ini
[Interface]
Address = 10.0.0.1/24
ListenPort = 51820
PrivateKey = <SERVER_PRIVATE_KEY>

[Peer]
# Agent 1
PublicKey = <AGENT_1_PUBLIC_KEY>
AllowedIPs = 10.0.0.2/32
```

Start the interface on the server:
```bash
sudo wg-quick up wg0
```

## 3. Agent Configuration

On each agent, generate keys:
```bash
wg genkey | tee agent_private.key | wg pubkey > agent_public.key
```

Create the agent's WireGuard configuration (`wg0.conf` for Linux or within the Windows GUI client):
```ini
[Interface]
Address = 10.0.0.2/32
PrivateKey = <AGENT_PRIVATE_KEY>

[Peer]
PublicKey = <SERVER_PUBLIC_KEY>
Endpoint = <SERVER_PUBLIC_IP>:51820
AllowedIPs = 10.0.0.0/24
PersistentKeepalive = 25
```

Bring up the interface on the Agent.

## 4. Connect Dragon S1
Once the VPN is active, configure your Dragon S1 Agents to connect to the Server using its VPN IP address (e.g., `http://10.0.0.1:3001` or `https://10.0.0.1:3001`) instead of its public IP. This ensures all traffic is encrypted at the network layer and hidden from the public internet.
