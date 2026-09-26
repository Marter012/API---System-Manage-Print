from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.websocket.manager import manager


router = APIRouter(tags=["WebSocket"])


async def handle_message(websocket: WebSocket, message: dict):
    message_type = message.get("type")

    if message_type == "ping":
        await manager.send_to(
            websocket,
            {
                "type": "pong",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        return

    if message_type == "REGISTER_PRINT_SERVER":
        manager.set_role(websocket, "print_server")

        await manager.send_to(
            websocket,
            {
                "type": "PRINT_SERVER_REGISTERED",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        cached_status = manager.print_server_status

        if cached_status is not None:
            await manager.send_to(
                websocket,
                {
                    "type": "PRINT_STATUS",
                    "data": cached_status,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

        return

    if message_type == "PRINT_STATUS":
        if manager.get_role(websocket) != "print_server":
            return

        status = message.get("data")

        if not isinstance(status, dict):
            return

        manager.set_print_server_status(status)

        await manager.broadcast(
            {
                "type": "PRINT_STATUS",
                "data": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        return

    if message_type == "PRINT_REQUEST":
        print_server = manager.get_print_server()
        request_id = message.get("request_id")
        source_client_id = manager.get_client_id(websocket)
        ticket = message.get("ticket")

        if not isinstance(ticket, str) or not ticket.strip():
            await manager.send_to(
                websocket,
                {
                    "type": "PRINT_RESULT",
                    "request_id": request_id,
                    "success": False,
                    "error": "El ticket de impresión está vacío.",
                },
            )
            return

        if print_server is None:
            await manager.send_to(
                websocket,
                {
                    "type": "PRINT_RESULT",
                    "request_id": request_id,
                    "success": False,
                    "error": "No hay una PC con el Print Agent conectado.",
                },
            )
            return

        delivered = await manager.send_to(
            print_server,
            {
                "type": "PRINT_REQUEST",
                "request_id": request_id,
                "source_client_id": source_client_id,
                "ticket": ticket,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        if not delivered:
            await manager.send_to(
                websocket,
                {
                    "type": "PRINT_RESULT",
                    "request_id": request_id,
                    "success": False,
                    "error": "No se pudo contactar la PC con el Print Agent.",
                },
            )

        return

    if message_type == "PRINT_RESULT":
        if manager.get_role(websocket) != "print_server":
            return

        request_id = message.get("request_id")
        source_client_id = message.get("source_client_id")

        result = {
            "type": "PRINT_RESULT",
            "request_id": request_id,
            "success": bool(message.get("success")),
        }

        if "response" in message:
            result["response"] = message["response"]

        if "error" in message:
            result["error"] = message["error"]

        await manager.send_to_client(source_client_id, result)
        return


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str | None = Query(default=None),
):
    client_id = client_id or str(uuid4())

    await manager.connect(websocket, client_id)

    try:
        while True:
            raw_message = await websocket.receive_text()

            try:
                import json

                message = json.loads(raw_message)
            except (json.JSONDecodeError, TypeError):
                continue

            if isinstance(message, dict):
                await handle_message(websocket, message)

    except WebSocketDisconnect:
        was_print_server = manager.get_role(websocket) == "print_server"
        manager.disconnect(websocket)

        if was_print_server:
            await manager.broadcast(
                {
                    "type": "PRINT_STATUS",
                    "data": {
                        "agent_connected": False,
                        "connected": False,
                        "online": False,
                        "status": "DISCONNECTED",
                        "status_message": "El Print Agent no está conectado.",
                        "printer": "",
                        "printer_type": "",
                        "driver": None,
                        "server": None,
                        "queue_count": 0,
                        "jobs": [],
                        "agent_queue_count": 0,
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

    except Exception:
        was_print_server = manager.get_role(websocket) == "print_server"
        manager.disconnect(websocket)

        if was_print_server:
            await manager.broadcast(
                {
                    "type": "PRINT_STATUS",
                    "data": {
                        "agent_connected": False,
                        "connected": False,
                        "online": False,
                        "status": "DISCONNECTED",
                        "status_message": "El Print Agent no está conectado.",
                        "printer": "",
                        "printer_type": "",
                        "driver": None,
                        "server": None,
                        "queue_count": 0,
                        "jobs": [],
                        "agent_queue_count": 0,
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
