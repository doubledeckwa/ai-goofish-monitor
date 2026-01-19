"""
WebSocket routing
Provide real-time communication capabilities
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set


router = APIRouter()

# overall situation WebSocket Connection management
active_connections: Set[WebSocket] = set()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
):
    """WebSocket endpoint"""
    # accept connection
    await websocket.accept()
    active_connections.add(websocket)

    try:
        # Stay connected and receive messages
        while True:
            # Receive client messages (if any）
            data = await websocket.receive_text()
            # Messages sent by the client can be processed here
            # At present, we mainly use it for server-side push, so we will not deal with it for the time being.
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        print(f"WebSocket mistake: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)


async def broadcast_message(message_type: str, data: dict):
    """Broadcast a message to all connected clients"""
    message = {
        "type": message_type,
        "data": data
    }

    # Remove broken connection
    disconnected = set()

    for connection in active_connections:
        try:
            await connection.send_json(message)
        except Exception:
            disconnected.add(connection)

    # Clean up broken connections
    for connection in disconnected:
        active_connections.discard(connection)
