from __future__ import annotations

import asyncio
from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.admins: set[WebSocket] = set()
        self.agents: dict[str, set[WebSocket]] = defaultdict(set)
        self.lock = asyncio.Lock()

    async def connect_admin(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self.lock:
            self.admins.add(websocket)

    async def disconnect_admin(self, websocket: WebSocket) -> None:
        async with self.lock:
            self.admins.discard(websocket)

    async def connect_agent(self, device_uid: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self.lock:
            self.agents[device_uid].add(websocket)

    async def disconnect_agent(self, device_uid: str, websocket: WebSocket) -> None:
        async with self.lock:
            self.agents[device_uid].discard(websocket)
            if not self.agents[device_uid]:
                self.agents.pop(device_uid, None)

    async def broadcast_admin(self, payload: dict) -> None:
        stale = []
        for socket in list(self.admins):
            try:
                await socket.send_json(payload)
            except Exception:
                stale.append(socket)
        for socket in stale:
            await self.disconnect_admin(socket)

    async def send_agent(self, device_uid: str, payload: dict) -> None:
        stale = []
        for socket in list(self.agents.get(device_uid, set())):
            try:
                await socket.send_json(payload)
            except Exception:
                stale.append(socket)
        for socket in stale:
            await self.disconnect_agent(device_uid, socket)


manager = ConnectionManager()
