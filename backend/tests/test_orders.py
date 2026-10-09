from decimal import Decimal

from app.models.user import UserRole


def money(value):
    return Decimal(str(value))


def find_table(client, headers, table_id):
    return next(t for t in client.get("/tables/", headers=headers).json() if t["id"] == table_id)


# ---------- Création (RM01, RM02, RM08, RM09) ----------

def test_create_order_computes_total_and_occupies_table(client, menu, serveur, serveur_headers, create_order):
    order = create_order(serveur_headers)
    assert order["status"] == "NEW"
    assert money(order["total"]) == Decimal("31.00")  # 2 x 12.50 + 2 x 3.00
    assert len(order["items"]) == 2
    assert order["sent_to_kitchen_at"] is None
    assert order["server_id"] == serveur.id
    assert find_table(client, serveur_headers, menu.table_id)["status"] == "OCCUPIED"


def test_unit_price_is_frozen_at_order_time(client, menu, serveur_headers, admin_headers, create_order):
    order = create_order(serveur_headers)
    client.put(f"/menu-items/{menu.pizza_id}", json={"price": 20}, headers=admin_headers)

    same_order = client.get(f"/orders/{order['id']}", headers=serveur_headers).json()
    assert money(same_order["total"]) == Decimal("31.00")
    pizza_line = next(i for i in same_order["items"] if i["menu_item_name"] == "Pizza Margherita")
    assert money(pizza_line["unit_price"]) == Decimal("12.50")


def test_unavailable_dish_is_refused_without_side_effects(client, menu, serveur_headers):
    payload = {"table_id": menu.table_id, "items": [{"menu_item_id": menu.tiramisu_id, "quantity": 1}]}
    res = client.post("/orders/", json=payload, headers=serveur_headers)
    assert res.status_code == 400
    assert client.get("/orders/", headers=serveur_headers).json() == []
    assert find_table(client, serveur_headers, menu.table_id)["status"] == "FREE"


def test_unknown_dish_is_refused(client, menu, serveur_headers):
    payload = {"table_id": menu.table_id, "items": [{"menu_item_id": 9999, "quantity": 1}]}
    assert client.post("/orders/", json=payload, headers=serveur_headers).status_code == 400


def test_empty_order_is_refused(client, menu, serveur_headers):
    payload = {"table_id": menu.table_id, "items": []}
    assert client.post("/orders/", json=payload, headers=serveur_headers).status_code == 422


def test_zero_quantity_is_refused(client, menu, serveur_headers):
    payload = {"table_id": menu.table_id, "items": [{"menu_item_id": menu.pizza_id, "quantity": 0}]}
    assert client.post("/orders/", json=payload, headers=serveur_headers).status_code == 422


def test_unknown_table_is_refused(client, menu, serveur_headers):
    payload = {"table_id": 9999, "items": [{"menu_item_id": menu.pizza_id, "quantity": 1}]}
    assert client.post("/orders/", json=payload, headers=serveur_headers).status_code == 400


def test_kitchen_staff_cannot_create_orders(client, menu, cuisine_headers):
    payload = {"table_id": menu.table_id, "items": [{"menu_item_id": menu.pizza_id, "quantity": 1}]}
    assert client.post("/orders/", json=payload, headers=cuisine_headers).status_code == 403


# ---------- Modification avant envoi (RM03, RM04) ----------

def test_replacing_items_recomputes_total(client, menu, serveur_headers, create_order):
    order = create_order(serveur_headers)
    res = client.put(
        f"/orders/{order['id']}/items",
        json={"items": [{"menu_item_id": menu.pizza_id, "quantity": 1}]},
        headers=serveur_headers,
    )
    assert res.status_code == 200
    assert money(res.json()["total"]) == Decimal("12.50")
    assert len(res.json()["items"]) == 1


def test_replacing_with_unavailable_dish_is_refused(client, menu, serveur_headers, create_order):
    order = create_order(serveur_headers)
    res = client.put(
        f"/orders/{order['id']}/items",
        json={"items": [{"menu_item_id": menu.tiramisu_id, "quantity": 1}]},
        headers=serveur_headers,
    )
    assert res.status_code == 400
    unchanged = client.get(f"/orders/{order['id']}", headers=serveur_headers).json()
    assert money(unchanged["total"]) == Decimal("31.00")


def test_order_cannot_be_modified_after_sending_to_kitchen(client, menu, serveur_headers, create_order):
    order = create_order(serveur_headers)
    sent = client.post(f"/orders/{order['id']}/send-to-kitchen", headers=serveur_headers)
    assert sent.status_code == 200
    assert sent.json()["sent_to_kitchen_at"] is not None

    res = client.put(
        f"/orders/{order['id']}/items",
        json={"items": [{"menu_item_id": menu.pizza_id, "quantity": 5}]},
        headers=serveur_headers,
    )
    assert res.status_code == 400


def test_order_cannot_be_sent_twice(client, serveur_headers, create_order):
    order = create_order(serveur_headers)
    assert client.post(f"/orders/{order['id']}/send-to-kitchen", headers=serveur_headers).status_code == 200
    assert client.post(f"/orders/{order['id']}/send-to-kitchen", headers=serveur_headers).status_code == 400


# ---------- Workflow des statuts (RM07) ----------

def test_full_workflow_with_correct_roles_and_timestamps(client, serveur_headers, cuisine_headers, create_order):
    order = create_order(serveur_headers)
    oid = order["id"]
    client.post(f"/orders/{oid}/send-to-kitchen", headers=serveur_headers)

    started = client.put(f"/orders/{oid}/status", json={"status": "IN_PREPARATION"}, headers=cuisine_headers)
    assert started.status_code == 200
    assert started.json()["preparation_started_at"] is not None

    ready = client.put(f"/orders/{oid}/status", json={"status": "READY"}, headers=cuisine_headers)
    assert ready.status_code == 200
    assert ready.json()["ready_at"] is not None

    served = client.put(f"/orders/{oid}/status", json={"status": "SERVED"}, headers=serveur_headers)
    assert served.status_code == 200
    assert served.json()["status"] == "SERVED"


def test_waiter_cannot_start_preparation(client, serveur_headers, create_order):
    order = create_order(serveur_headers)
    client.post(f"/orders/{order['id']}/send-to-kitchen", headers=serveur_headers)
    res = client.put(f"/orders/{order['id']}/status", json={"status": "IN_PREPARATION"}, headers=serveur_headers)
    assert res.status_code == 403


def test_kitchen_cannot_mark_order_as_served(client, serveur_headers, cuisine_headers, create_order):
    order = create_order(serveur_headers)
    oid = order["id"]
    client.post(f"/orders/{oid}/send-to-kitchen", headers=serveur_headers)
    client.put(f"/orders/{oid}/status", json={"status": "IN_PREPARATION"}, headers=cuisine_headers)
    client.put(f"/orders/{oid}/status", json={"status": "READY"}, headers=cuisine_headers)
    res = client.put(f"/orders/{oid}/status", json={"status": "SERVED"}, headers=cuisine_headers)
    assert res.status_code == 403


def test_cannot_skip_a_status(client, serveur_headers, cuisine_headers, create_order):
    order = create_order(serveur_headers)
    client.post(f"/orders/{order['id']}/send-to-kitchen", headers=serveur_headers)
    res = client.put(f"/orders/{order['id']}/status", json={"status": "READY"}, headers=cuisine_headers)
    assert res.status_code == 400


def test_cannot_prepare_an_order_not_sent_to_kitchen(client, serveur_headers, cuisine_headers, create_order):
    order = create_order(serveur_headers)
    res = client.put(f"/orders/{order['id']}/status", json={"status": "IN_PREPARATION"}, headers=cuisine_headers)
    assert res.status_code == 400


def test_status_of_unknown_order_returns_404(client, cuisine_headers):
    res = client.put("/orders/9999/status", json={"status": "IN_PREPARATION"}, headers=cuisine_headers)
    assert res.status_code == 404


# ---------- Tables : libération manuelle ----------

def test_table_stays_occupied_after_service(client, menu, serveur_headers, create_order, run_full_service):
    order = create_order(serveur_headers)
    run_full_service(order["id"])
    assert find_table(client, serveur_headers, menu.table_id)["status"] == "OCCUPIED"


def test_waiter_can_free_a_table(client, menu, serveur_headers, create_order, run_full_service):
    """Le bouton 'Libérer la table' du serveur doit fonctionner."""
    order = create_order(serveur_headers)
    run_full_service(order["id"])

    res = client.put(f"/tables/{menu.table_id}", json={"status": "FREE"}, headers=serveur_headers)
    assert res.status_code == 200, "Un serveur doit pouvoir libérer une table"
    assert find_table(client, serveur_headers, menu.table_id)["status"] == "FREE"


# ---------- Filtres de consultation ----------

def test_mine_only_and_kitchen_view_filters(
    client, menu, make_user, auth_headers, serveur_headers, cuisine_headers, create_order
):
    other_headers = auth_headers(make_user(UserRole.SERVEUR))
    mine = create_order(serveur_headers)
    create_order(other_headers)

    mine_only = client.get("/orders/?mine_only=true", headers=serveur_headers).json()
    assert [o["id"] for o in mine_only] == [mine["id"]]

    # Aucune commande envoyée : la cuisine ne voit encore rien
    assert client.get("/orders/?kitchen_view=true", headers=cuisine_headers).json() == []

    client.post(f"/orders/{mine['id']}/send-to-kitchen", headers=serveur_headers)
    kitchen = client.get("/orders/?kitchen_view=true", headers=cuisine_headers).json()
    assert [o["id"] for o in kitchen] == [mine["id"]]


def test_unknown_order_returns_404(client, serveur_headers):
    assert client.get("/orders/9999", headers=serveur_headers).status_code == 404