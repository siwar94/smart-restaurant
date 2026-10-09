"""Génère un historique de commandes synthétique pour tester le pipeline IA.
Usage : python scripts/seed_historical_orders.py
"""
import random
from datetime import datetime, timedelta, timezone

from app.database.session import SessionLocal
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.menu_item import MenuItem
from app.models.restaurant_table import RestaurantTable
from app.models.user import User, UserRole


def pick_hour() -> int:
    """Simule deux pics d'affluence : déjeuner (12-14h) et dîner (19-21h)."""
    r = random.random()
    if r < 0.45:
        return random.randint(12, 14)
    elif r < 0.85:
        return random.randint(19, 21)
    else:
        return random.choice([11, 15, 16, 17, 18, 22])


def seed_historical_orders(days_back: int = 90, avg_orders_per_day: int = 15):
    db = SessionLocal()
    try:
        tables = db.query(RestaurantTable).all()
        menu_items = db.query(MenuItem).filter(MenuItem.available == True).all()
        server = db.query(User).filter(User.role == UserRole.SERVEUR).first()

        if not tables or not menu_items or not server:
            print("⚠️  Il faut au moins une table, un plat disponible et un serveur en base "
                  "avant de lancer ce script.")
            return

        created_count = 0
        now = datetime.now(timezone.utc)

        for day_offset in range(days_back, 0, -1):
            day = now - timedelta(days=day_offset)
            weekday = day.weekday()  # 0=lundi ... 6=dimanche

            # Vendredi soir, samedi, dimanche : affluence plus forte
            day_multiplier = 1.6 if weekday in (4, 5, 6) else 1.0
            orders_today = max(1, int(random.gauss(avg_orders_per_day * day_multiplier, 4)))

            for _ in range(orders_today):
                hour = pick_hour()
                created_at = day.replace(hour=hour, minute=random.randint(0, 59), second=0, microsecond=0)

                table = random.choice(tables)
                items_for_order = random.sample(menu_items, k=min(len(menu_items), random.randint(1, 3)))

                order_items = []
                total = 0.0
                for item in items_for_order:
                    qty = random.randint(1, 3)
                    order_items.append(OrderItem(menu_item_id=item.id, quantity=qty, unit_price=item.price))
                    total += qty * float(item.price)

                sent_to_kitchen_at = created_at + timedelta(minutes=random.randint(1, 5))
                preparation_started_at = sent_to_kitchen_at + timedelta(minutes=random.randint(1, 4))
                ready_at = preparation_started_at + timedelta(minutes=random.randint(8, 20))

                order = Order(
                    table_id=table.id,
                    server_id=server.id,
                    status=OrderStatus.SERVED,
                    total=total,
                    created_at=created_at,
                    sent_to_kitchen_at=sent_to_kitchen_at,
                    preparation_started_at=preparation_started_at,
                    ready_at=ready_at,
                    items=order_items,
                )
                db.add(order)
                created_count += 1

        db.commit()
        print(f"✅ {created_count} commandes historiques générées sur {days_back} jours.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_historical_orders()