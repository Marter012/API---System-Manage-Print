from uuid import uuid4

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.websocket.manager import manager


router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str | None = Query(default=None),
):
    client_id = client_id or str(uuid4())

    await manager.connect(websocket, client_id)

    try:
        while True:
            # El navegador manda pequeños mensajes de heartbeat.
            # No necesitamos procesarlos: recibirlos mantiene viva la conexión.
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)

    except Exception:
        manager.disconnect(websocket)
