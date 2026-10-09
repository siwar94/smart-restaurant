from app.models.user import User, UserRole


def test_admin_can_list_users(client, admin_headers):
    res = client.get("/users/", headers=admin_headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_non_admins_cannot_list_or_create_users(client, serveur_headers, cuisine_headers):
    payload = {"name": "X", "email": "x@test.com", "password": "pw123456", "role": "SERVEUR"}
    assert client.get("/users/", headers=serveur_headers).status_code == 403
    assert client.get("/users/", headers=cuisine_headers).status_code == 403
    assert client.post("/users/", json=payload, headers=serveur_headers).status_code == 403


def test_admin_creates_user_who_can_then_log_in(client, db, admin_headers):
    payload = {"name": "Nouveau", "email": "nouveau@test.com", "password": "pw-12345", "role": "CUISINE"}
    res = client.post("/users/", json=payload, headers=admin_headers)
    assert res.status_code == 201
    body = res.json()
    assert body["email"] == "nouveau@test.com"
    assert body["role"] == "CUISINE"
    assert "password" not in body and "password_hash" not in body

    stored = db.query(User).filter(User.email == "nouveau@test.com").one()
    assert stored.password_hash != "pw-12345"  # jamais stocké en clair

    login = client.post("/auth/login", json={"email": "nouveau@test.com", "password": "pw-12345"})
    assert login.status_code == 200


def test_duplicate_email_is_refused(client, admin_headers, serveur):
    payload = {"name": "Doublon", "email": serveur.email, "password": "pw123456", "role": "SERVEUR"}
    assert client.post("/users/", json=payload, headers=admin_headers).status_code == 400


def test_admin_can_change_a_role(client, admin_headers, serveur):
    res = client.put(f"/users/{serveur.id}", json={"role": "CUISINE"}, headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["role"] == "CUISINE"


def test_delete_deactivates_instead_of_removing(client, db, admin_headers, serveur):
    assert client.delete(f"/users/{serveur.id}", headers=admin_headers).status_code == 204
    db.expire_all()
    stored = db.get(User, serveur.id)
    assert stored is not None and stored.is_active is False


def test_unknown_user_returns_404(client, admin_headers):
    assert client.get("/users/9999", headers=admin_headers).status_code == 404