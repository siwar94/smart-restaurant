def test_forecast_is_admin_only(client, serveur_headers):
    assert client.get("/ai/demand-forecast", headers=serveur_headers).status_code == 403


def test_forecast_returns_predictions_or_503_when_model_is_missing(client, menu, admin_headers):
    res = client.get("/ai/demand-forecast", headers=admin_headers)
    assert res.status_code in (200, 503)
    if res.status_code == 200:
        body = res.json()
        assert "date" in body
        assert all(item["predicted_quantity"] >= 0 for item in body["items"])


def test_item_recommendations_never_block_the_waiter(client, menu, serveur_headers):
    res = client.get(f"/ai/recommendations/{menu.pizza_id}", headers=serveur_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_global_recommendations_are_admin_only(client, serveur_headers):
    assert client.get("/ai/recommendations", headers=serveur_headers).status_code == 403