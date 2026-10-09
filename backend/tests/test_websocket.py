import time

import pytest
from starlette.websockets import WebSocketDisconnect

from app.core.security import create_access_token
from app.core.ws_manager import manager


def wait_until(condition, timeout=2.0):
    end = time.time() + timeout
    while time.time() < end:
        if condition():
            return True
        time.sleep(0.02)
    return False


def test_websocket_rejects_invalid_token(client):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws?token=pas-un-jwt"):
            pass


def test_websocket_rejects_missing_token(client):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws"):
            pass


def test_websocket_registers_the_authenticated_user(client, serveur):
    token = create_access_token({"sub": str(serveur.id), "role": "SERVEUR"})
    with client.websocket_connect(f"/ws?token={token}"):
        assert wait_until(lambda: serveur.id in manager.connections_by_user)