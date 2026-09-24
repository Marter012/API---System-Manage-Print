from datetime import datetime, timezone
from typing import Any

from fastapi.encoders import jsonable_encoder

from app.websocket.manager import manager


async def broadcast_change(
    resource: str,
    action: str,
    data: Any = None,
    source_client_id: str | None = None,
):
    """Publica un cambio de datos a todos los clientes conectados."""

    message = {
        "type": "DATA_CHANGED",
        "resource": resource,
        "action": action,
        "data": jsonable_encoder(data),
        "source_client_id": source_client_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    await manager.broadcast(message)
