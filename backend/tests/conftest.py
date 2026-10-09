import itertools
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.main import app  # importe aussi tous les routers/modèles -> Base.metadata complète
from app.core.config import settings
from app.core.security import hash_password
from app.database.session import Base, get_db
from app.models.category import Category
from app.models.menu_item import MenuItem
from app.models.restaurant_table import RestaurantTable, TableStatus
from app.models.user import User, UserRole

_counter = itertools.count(1)


@pytest.fixture(scope="session", autouse=True)
def fast_password_hashing():
    """bcrypt avec 4 rounds au lieu de 12 : la suite tourne ~50x plus vite."""
    import bcrypt

    original = bcrypt.gensalt
    bcrypt.gensalt = lambda rounds=4, prefix=b"2b": original(rounds=rounds, prefix=prefix)
    yield
    bcrypt.gensalt = original


@pytest.fixture(scope="session")
def test_engine():
    """Base PostgreSQL dédiée aux tests : <ta_base>_test (créée si absente)."""
    base_url = make_url(settings.DATABASE_URL)
    test_url = base_url.set(database=f"{base_url.database}_test")

    admin_engine = create_engine(base_url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": test_url.database},
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{test_url.database}"'))
    admin_engine.dispose()

    engine = create_engine(test_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_database(test_engine):
    """Vide toutes les tables après chaque test : isolation totale."""
    yield
    tables = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
    with test_engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture
def session_factory(test_engine):
    return sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


@pytest.fixture
def db(session_factory):
    session = session_factory()
    yield session
    session.close()


@pytest.fixture
def client(session_factory):
    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:  # un seul event loop partagé (utile pour le WebSocket)
        yield test_client
    app.dependency_overrides.clear()


# ---------- Utilisateurs ----------

@pytest.fixture
def make_user(db):
    def _make(role=UserRole.SERVEUR, email=None, password="secret123", name=None, is_active=True):
        n = next(_counter)
        user = User(
            name=name or f"{role.value.title()} {n}",
            email=email or f"{role.value.lower()}{n}@test.com",
            password_hash=hash_password(password),
            role=role,
            is_active=is_active,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user.plain_password = password  # pratique pour se connecter dans les tests
        return user

    return _make


@pytest.fixture
def auth_headers(client):
    def _headers(user):
        res = client.post("/auth/login", json={"email": user.email, "password": user.plain_password})
        assert res.status_code == 200, res.text
        return {"Authorization": f"Bearer {res.json()['access_token']}"}

    return _headers


@pytest.fixture
def admin(make_user):
    return make_user(UserRole.ADMIN)


@pytest.fixture
def serveur(make_user):
    return make_user(UserRole.SERVEUR)


@pytest.fixture
def cuisine(make_user):
    return make_user(UserRole.CUISINE)


@pytest.fixture
def admin_headers(admin, auth_headers):
    return auth_headers(admin)


@pytest.fixture
def serveur_headers(serveur, auth_headers):
    return auth_headers(serveur)


@pytest.fixture
def cuisine_headers(cuisine, auth_headers):
    return auth_headers(cuisine)


# ---------- Données de démonstration ----------

@pytest.fixture
def menu(db):
    """1 catégorie, 2 plats disponibles (12.50 / 3.00), 1 plat indisponible, 1 table libre."""
    category = Category(name="Plats")
    db.add(category)
    db.commit()
    db.refresh(category)

    pizza = MenuItem(name="Pizza Margherita", description="Classique", price=Decimal("12.50"),
                     category_id=category.id, available=True)
    coca = MenuItem(name="Coca-Cola", description="33cl", price=Decimal("3.00"),
                    category_id=category.id, available=True)
    tiramisu = MenuItem(name="Tiramisu", description="Dessert", price=Decimal("8.50"),
                        category_id=category.id, available=False)
    table = RestaurantTable(number=1, status=TableStatus.FREE)
    db.add_all([pizza, coca, tiramisu, table])
    db.commit()
    for obj in (pizza, coca, tiramisu, table):
        db.refresh(obj)

    return SimpleNamespace(
        category_id=category.id,
        pizza_id=pizza.id,
        coca_id=coca.id,
        tiramisu_id=tiramisu.id,
        table_id=table.id,
    )


@pytest.fixture
def create_order(client, menu):
    """Crée une commande (2 pizzas + 2 cocas = 31.00 par défaut)."""
    def _create(headers, items=None, table_id=None):
        payload = {
            "table_id": table_id or menu.table_id,
            "items": items or [
                {"menu_item_id": menu.pizza_id, "quantity": 2},
                {"menu_item_id": menu.coca_id, "quantity": 2},
            ],
        }
        res = client.post("/orders/", json=payload, headers=headers)
        assert res.status_code == 201, res.text
        return res.json()

    return _create


@pytest.fixture
def run_full_service(client, serveur_headers, cuisine_headers):
    """Fait passer une commande NEW -> cuisine -> IN_PREPARATION -> READY -> SERVED."""
    def _run(order_id):
        res = client.post(f"/orders/{order_id}/send-to-kitchen", headers=serveur_headers)
        assert res.status_code == 200, res.text
        for headers, status in (
            (cuisine_headers, "IN_PREPARATION"),
            (cuisine_headers, "READY"),
            (serveur_headers, "SERVED"),
        ):
            res = client.put(f"/orders/{order_id}/status", json={"status": status}, headers=headers)
            assert res.status_code == 200, res.text

    return _run