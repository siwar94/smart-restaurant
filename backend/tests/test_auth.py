from app.core.security import create_access_token, decode_access_token
from app.models.user import UserRole


def test_login_returns_token_with_user_id_and_role(client, admin):
    res = client.post("/auth/login", json={"email": admin.email, "password": admin.plain_password})
    assert res.status_code == 200
    payload = decode_access_token(res.json()["access_token"])
    assert payload["sub"] == str(admin.id)
    assert payload["role"] == "ADMIN"


def test_login_with_wrong_password_is_refused(client, admin):
    res = client.post("/auth/login", json={"email": admin.email, "password": "mauvais"})
    assert res.status_code in (400, 401)
    assert "access_token" not in res.json()


def test_login_with_unknown_email_is_refused(client):
    res = client.post("/auth/login", json={"email": "inconnu@test.com", "password": "x"})
    assert res.status_code in (400, 401)


def test_deactivated_user_cannot_log_in(client, make_user):
    user = make_user(UserRole.SERVEUR, is_active=False)
    res = client.post("/auth/login", json={"email": user.email, "password": user.plain_password})
    assert res.status_code in (400, 401, 403)


def test_protected_route_without_token_is_refused(client):
    assert client.get("/users/").status_code in (401, 403)


def test_garbage_token_is_refused(client):
    res = client.get("/users/", headers={"Authorization": "Bearer nimportequoi"})
    assert res.status_code == 401


def test_token_of_unknown_user_is_refused(client):
    token = create_access_token({"sub": "9999", "role": "ADMIN"})
    res = client.get("/users/", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401


def test_role_is_read_from_database_not_from_token(client, serveur):
    """Un serveur qui forge un token 'ADMIN' (avec la vraie clé) ne gagne aucun droit."""
    forged = create_access_token({"sub": str(serveur.id), "role": "ADMIN"})
    res = client.get("/users/", headers={"Authorization": f"Bearer {forged}"})
    assert res.status_code == 403


def test_token_of_deactivated_user_is_refused(client, make_user, auth_headers, admin_headers):
    waiter = make_user(UserRole.SERVEUR)
    waiter_headers = auth_headers(waiter)
    assert client.get("/orders/", headers=waiter_headers).status_code == 200

    assert client.delete(f"/users/{waiter.id}", headers=admin_headers).status_code == 204
    assert client.get("/orders/", headers=waiter_headers).status_code == 401