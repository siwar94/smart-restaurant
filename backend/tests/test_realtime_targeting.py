import pytest

from app.core.ws_manager import manager
from app.models.user import UserRole


@pytest.fixture
def notifications(monkeypatch):
    """Enregistre les notifications au lieu de les envoyer sur de vrais WebSockets."""
    calls = []

    async def fake_send_to_user(user_id, message):
        calls.append(("user", user_id, message))

    async def fake_broadcast_to_roles(message, user_ids):
        calls.append(("roles", set(user_ids), message))

    monkeypatch.setattr(manager, "send_to_user", fake_send_to_user)
    monkeypatch.setattr(manager, "broadcast_to_roles", fake_broadcast_to_roles)
    return calls


def test_kitchen_and_admin_are_notified_of_new_and_sent_orders(
    client, admin, cuisine, serveur, serveur_headers, create_order, notifications
):
    order = create_order(serveur_headers)
    kind, recipients, message = notifications[-1]
    assert kind == "roles"
    assert recipients == {admin.id, cuisine.id}  # jamais un serveur
    assert message["type"] == "order_created"

    client.post(f"/orders/{order['id']}/send-to-kitchen", headers=serveur_headers)
    kind, recipients, message = notifications[-1]
    assert kind == "roles"
    assert recipients == {admin.id, cuisine.id}
    assert message["type"] == "order_sent_to_kitchen"


def test_ready_notification_goes_only_to_the_owning_waiter(
    client, admin, cuisine, serveur, make_user, auth_headers,
    serveur_headers, cuisine_headers, create_order, notifications
):
    other_waiter = make_user(UserRole.SERVEUR)
    order = create_order(serveur_headers)
    client.post(f"/orders/{order['id']}/send-to-kitchen", headers=serveur_headers)
    client.put(f"/orders/{order['id']}/status", json={"status": "IN_PREPARATION"}, headers=cuisine_headers)

    notifications.clear()
    client.put(f"/orders/{order['id']}/status", json={"status": "READY"}, headers=cuisine_headers)

    assert len(notifications) == 1
    kind, target, message = notifications[0]
    assert kind == "user"
    assert target == serveur.id          # le propriétaire de la commande...
    assert target != other_waiter.id     # ...et pas un autre serveur
    assert message["status"] == "READY"


def test_in_preparation_and_served_events_go_to_kitchen_and_admin(
    client, admin, cuisine, serveur_headers, cuisine_headers, create_order, notifications
):
    order = create_order(serveur_headers)
    client.post(f"/orders/{order['id']}/send-to-kitchen", headers=serveur_headers)

    notifications.clear()
    client.put(f"/orders/{order['id']}/status", json={"status": "IN_PREPARATION"}, headers=cuisine_headers)
    assert notifications[0][0] == "roles" and notifications[0][1] == {admin.id, cuisine.id}