import asyncio
import json

from app.core.ws_manager import ConnectionManager


class FakeWebSocket:
    def __init__(self, fail=False):
        self.accepted = False
        self.messages = []
        self.fail = fail

    async def accept(self):
        self.accepted = True

    async def send_text(self, payload):
        if self.fail:
            raise RuntimeError("connexion coupée")
        self.messages.append(json.loads(payload))


def test_send_to_user_reaches_only_that_user():
    async def scenario():
        manager = ConnectionManager()
        ws_a, ws_b = FakeWebSocket(), FakeWebSocket()
        await manager.connect(ws_a, user_id=1)
        await manager.connect(ws_b, user_id=2)
        await manager.send_to_user(1, {"type": "order_ready"})
        return ws_a, ws_b

    ws_a, ws_b = asyncio.run(scenario())
    assert ws_a.messages == [{"type": "order_ready"}]
    assert ws_b.messages == []


def test_same_user_on_two_devices_receives_on_both():
    async def scenario():
        manager = ConnectionManager()
        tab1, tab2 = FakeWebSocket(), FakeWebSocket()
        await manager.connect(tab1, user_id=1)
        await manager.connect(tab2, user_id=1)
        await manager.send_to_user(1, {"type": "x"})
        return tab1, tab2

    tab1, tab2 = asyncio.run(scenario())
    assert len(tab1.messages) == 1 and len(tab2.messages) == 1


def test_broadcast_to_roles_reaches_only_listed_users():
    async def scenario():
        manager = ConnectionManager()
        sockets = {uid: FakeWebSocket() for uid in (1, 2, 3)}
        for uid, ws in sockets.items():
            await manager.connect(ws, user_id=uid)
        await manager.broadcast_to_roles({"type": "order_created"}, [1, 3])
        return sockets

    sockets = asyncio.run(scenario())
    assert len(sockets[1].messages) == 1
    assert len(sockets[3].messages) == 1
    assert sockets[2].messages == []


def test_disconnect_cleans_up_user_entry():
    async def scenario():
        manager = ConnectionManager()
        ws = FakeWebSocket()
        await manager.connect(ws, user_id=1)
        manager.disconnect(ws, user_id=1)
        return manager

    assert 1 not in asyncio.run(scenario()).connections_by_user


def test_broken_connection_is_dropped_after_failed_send():
    async def scenario():
        manager = ConnectionManager()
        await manager.connect(FakeWebSocket(fail=True), user_id=1)
        await manager.send_to_user(1, {"type": "x"})
        return manager

    assert 1 not in asyncio.run(scenario()).connections_by_user


def test_sending_to_an_offline_user_does_not_crash():
    async def scenario():
        await ConnectionManager().send_to_user(999, {"type": "x"})

    asyncio.run(scenario())