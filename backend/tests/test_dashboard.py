from decimal import Decimal


def money(value):
    return Decimal(str(value))


def test_dashboard_is_admin_only(client, serveur_headers, cuisine_headers):
    assert client.get("/dashboard/", headers=serveur_headers).status_code == 403
    assert client.get("/dashboard/", headers=cuisine_headers).status_code == 403
    assert client.get("/dashboard/analytics", headers=serveur_headers).status_code == 403


def test_dashboard_on_empty_database(client, admin_headers):
    body = client.get("/dashboard/", headers=admin_headers).json()
    assert body["summary"]["orders_today"] == 0
    assert money(body["summary"]["revenue_today"]) == 0
    assert body["top_items"] == []
    assert body["preparation"]["orders_measured"] == 0
    assert body["preparation"]["average_preparation_seconds"] is None


def test_dashboard_after_a_full_service(client, menu, admin_headers, serveur_headers, create_order, run_full_service):
    order = create_order(serveur_headers)
    run_full_service(order["id"])

    body = client.get("/dashboard/", headers=admin_headers).json()
    summary = body["summary"]
    assert summary["orders_today"] == 1
    assert summary["orders_served_today"] == 1
    assert summary["orders_in_progress"] == 0
    assert money(summary["revenue_today"]) == Decimal("31.00")
    assert summary["occupied_tables"] == 1   # la table reste occupée tant que le serveur ne la libère pas
    assert summary["total_tables"] == 1

    top = {item["name"]: item for item in body["top_items"]}
    assert set(top) == {"Pizza Margherita", "Coca-Cola"}
    assert top["Pizza Margherita"]["total_quantity"] == 2
    assert money(top["Pizza Margherita"]["total_revenue"]) == Decimal("25.00")
    assert money(top["Coca-Cola"]["total_revenue"]) == Decimal("6.00")

    prep = body["preparation"]
    assert prep["orders_measured"] == 1
    assert prep["average_preparation_seconds"] is not None
    assert prep["average_preparation_seconds"] >= 0


def test_in_progress_orders_are_not_counted_as_revenue(client, menu, admin_headers, serveur_headers, create_order):
    create_order(serveur_headers)  # jamais servie
    summary = client.get("/dashboard/", headers=admin_headers).json()["summary"]
    assert summary["orders_in_progress"] == 1
    assert money(summary["revenue_today"]) == 0


def test_analytics_has_one_point_per_day_and_24_hours(client, menu, admin_headers, serveur_headers, create_order):
    create_order(serveur_headers)
    body = client.get("/dashboard/analytics?days=7", headers=admin_headers).json()

    days = [p["date"] for p in body["orders_by_day"]]
    assert len(days) == 7
    assert days == sorted(days)
    assert sum(p["orders_count"] for p in body["orders_by_day"]) == 1

    assert [p["hour"] for p in body["peak_hours"]] == list(range(24))
    assert sum(p["orders_count"] for p in body["peak_hours"]) == 1