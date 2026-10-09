import pytest


def test_everyone_can_read_menu_but_only_admin_can_write(client, menu, serveur_headers, cuisine_headers):
    assert client.get("/categories/", headers=serveur_headers).status_code == 200
    assert client.get("/menu-items/", headers=cuisine_headers).status_code == 200

    new_item = {"name": "Salade", "price": 6.5, "category_id": menu.category_id, "available": True}
    assert client.post("/menu-items/", json=new_item, headers=serveur_headers).status_code == 403
    assert client.post("/categories/", json={"name": "Boissons"}, headers=serveur_headers).status_code == 403


def test_admin_manages_categories(client, admin_headers):
    created = client.post("/categories/", json={"name": "Desserts"}, headers=admin_headers)
    assert created.status_code == 201
    category_id = created.json()["id"]

    assert client.post("/categories/", json={"name": "Desserts"}, headers=admin_headers).status_code == 400  # doublon

    renamed = client.put(f"/categories/{category_id}", json={"name": "Douceurs"}, headers=admin_headers)
    assert renamed.json()["name"] == "Douceurs"

    assert client.delete(f"/categories/{category_id}", headers=admin_headers).status_code == 204
    assert client.get(f"/categories/{category_id}", headers=admin_headers).status_code == 404


def test_admin_creates_menu_item_with_nested_category(client, menu, admin_headers):
    payload = {"name": "Salade", "description": "Fraîche", "price": 6.5,
               "category_id": menu.category_id, "available": True}
    res = client.post("/menu-items/", json=payload, headers=admin_headers)
    assert res.status_code == 201
    assert res.json()["category"]["name"] == "Plats"


def test_menu_item_with_unknown_category_is_refused(client, admin_headers):
    payload = {"name": "Orphelin", "price": 5, "category_id": 9999, "available": True}
    assert client.post("/menu-items/", json=payload, headers=admin_headers).status_code == 400


def test_available_only_filter_hides_unavailable_items(client, menu, serveur_headers):
    everything = client.get("/menu-items/", headers=serveur_headers).json()
    available = client.get("/menu-items/?available_only=true", headers=serveur_headers).json()
    assert {i["name"] for i in everything} == {"Pizza Margherita", "Coca-Cola", "Tiramisu"}
    assert {i["name"] for i in available} == {"Pizza Margherita", "Coca-Cola"}


def test_admin_can_toggle_availability(client, menu, admin_headers, serveur_headers):
    client.put(f"/menu-items/{menu.pizza_id}", json={"available": False}, headers=admin_headers)
    available = client.get("/menu-items/?available_only=true", headers=serveur_headers).json()
    assert "Pizza Margherita" not in {i["name"] for i in available}


def test_unknown_menu_item_returns_404(client, admin_headers):
    assert client.get("/menu-items/9999", headers=admin_headers).status_code == 404


@pytest.mark.xfail(reason="Lacune connue : le backend n'interdit pas encore les prix négatifs", strict=False)
def test_negative_price_is_refused(client, menu, admin_headers):
    payload = {"name": "Erreur", "price": -5, "category_id": menu.category_id, "available": True}
    assert client.post("/menu-items/", json=payload, headers=admin_headers).status_code == 422