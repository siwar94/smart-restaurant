from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import jwt

from app.core.security import decode_access_token
from app.core.ws_manager import manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except jwt.PyJWTError:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, user_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)