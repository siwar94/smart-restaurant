import json
from typing import Dict, List

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # Une connexion peut appartenir à un utilisateur ; plusieurs onglets/appareils
        # du même utilisateur sont possibles, d'où une liste par user_id.
        self.connections_by_user: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.connections_by_user.setdefault(user_id, []).append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        connections = self.connections_by_user.get(user_id, [])
        if websocket in connections:
            connections.remove(websocket)
        if not connections and user_id in self.connections_by_user:
            del self.connections_by_user[user_id]

    async def send_to_user(self, user_id: int, message: dict):
        payload = json.dumps(message)
        stale = []
        for connection in self.connections_by_user.get(user_id, []):
            try:
                await connection.send_text(payload)
            except Exception:
                stale.append(connection)
        for connection in stale:
            self.disconnect(connection, user_id)

    async def broadcast_to_roles(self, message: dict, user_ids: List[int]):
        for user_id in user_ids:
            await self.send_to_user(user_id, message)


manager = ConnectionManager()