from typing import Dict

from fastapi import WebSocket


class ConnectionManager:
    """Mantiene las conexiones WebSocket activas del sistema."""

    def __init__(self):
        self.active_connections: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[websocket] = client_id

    def disconnect(self, websocket: WebSocket):
        self.active_connections.pop(websocket, None)

    async def broadcast(self, message: dict):
        disconnected = []

        for websocket in list(self.active_connections.keys()):
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect(websocket)

    def get_client_id(self, websocket: WebSocket) -> str | None:
        return self.active_connections.get(websocket)


manager = ConnectionManager()
