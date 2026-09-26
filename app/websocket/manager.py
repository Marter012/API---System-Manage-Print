from typing import Dict

from fastapi import WebSocket


class ConnectionManager:
    """Mantiene las conexiones WebSocket activas y el Print Host."""

    def __init__(self):
        self.active_connections: Dict[WebSocket, str] = {}
        self.roles: Dict[WebSocket, str] = {}
        self.print_server: WebSocket | None = None
        self.print_server_status: dict | None = None

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[websocket] = client_id
        self.roles[websocket] = "client"

    def disconnect(self, websocket: WebSocket):
        was_print_server = self.print_server is websocket

        self.active_connections.pop(websocket, None)
        self.roles.pop(websocket, None)

        if was_print_server:
            self.print_server = None
            self.print_server_status = None

    def get_client_id(self, websocket: WebSocket) -> str | None:
        return self.active_connections.get(websocket)

    def get_role(self, websocket: WebSocket) -> str | None:
        return self.roles.get(websocket)

    def set_role(self, websocket: WebSocket, role: str):
        if websocket not in self.active_connections:
            return

        if role == "print_server":
            if self.print_server is not None and self.print_server is not websocket:
                self.roles[self.print_server] = "client"

            self.print_server = websocket

        self.roles[websocket] = role

    def get_print_server(self) -> WebSocket | None:
        websocket = self.print_server

        if websocket is None:
            return None

        if websocket not in self.active_connections:
            self.print_server = None
            self.print_server_status = None
            return None

        return websocket

    def set_print_server_status(self, status: dict | None):
        self.print_server_status = status

    async def send_to(self, websocket: WebSocket | None, message: dict) -> bool:
        if websocket is None:
            return False

        if websocket not in self.active_connections:
            return False

        try:
            await websocket.send_json(message)
            return True
        except Exception:
            self.disconnect(websocket)
            return False

    async def send_to_client(self, client_id: str | None, message: dict) -> bool:
        if not client_id:
            return False

        for websocket, current_client_id in list(self.active_connections.items()):
            if current_client_id == client_id:
                return await self.send_to(websocket, message)

        return False

    async def broadcast(self, message: dict):
        disconnected = []

        for websocket in list(self.active_connections.keys()):
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect(websocket)


manager = ConnectionManager()
