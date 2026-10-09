"""Extrait l'historique des commandes SERVED depuis PostgreSQL et produit
deux fichiers CSV : un jeu de données brut, et un jeu agrégé par jour/plat
prêt pour l'entraînement d'un modèle de prévision de la demande.

Usage : python scripts/export_dataset.py
"""
import os

import pandas as pd

from app.database.session import SessionLocal
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.menu_item import MenuItem

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def export_raw_orders(db) -> pd.DataFrame:
    rows = (
        db.query(
            Order.id.label("order_id"),
            Order.created_at,
            Order.status,
            OrderItem.menu_item_id,
            MenuItem.name.label("menu_item_name"),
            OrderItem.quantity,
            OrderItem.unit_price,
        )
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(MenuItem, MenuItem.id == OrderItem.menu_item_id)
        .filter(Order.status == OrderStatus.SERVED)
        .all()
    )

    df = pd.DataFrame(
        rows,
        columns=[
            "order_id", "created_at", "status", "menu_item_id",
            "menu_item_name", "quantity", "unit_price",
        ],
    )
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["date"] = df["created_at"].dt.date
    df["day_of_week"] = df["created_at"].dt.dayofweek  # 0=lundi ... 6=dimanche
    df["hour"] = df["created_at"].dt.hour
    df["subtotal"] = df["quantity"] * df["unit_price"].astype(float)
    return df


def build_daily_demand(df: pd.DataFrame) -> pd.DataFrame:
    """Agrège en 'quantité vendue par plat et par jour' — le format
    attendu pour entraîner un modèle de prévision de la demande (Étape 17)."""
    daily = (
        df.groupby(["date", "day_of_week", "menu_item_id", "menu_item_name"])
        .agg(total_quantity=("quantity", "sum"), total_revenue=("subtotal", "sum"))
        .reset_index()
    )
    return daily


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    db = SessionLocal()
    try:
        raw_df = export_raw_orders(db)
        if raw_df.empty:
            print(
                "⚠️  Aucune commande SERVED en base. Lance d'abord "
                "scripts/seed_historical_orders.py (ou attends d'avoir assez d'historique réel)."
            )
            return

        daily_df = build_daily_demand(raw_df)

        raw_path = os.path.join(OUTPUT_DIR, "orders_raw.csv")
        daily_path = os.path.join(OUTPUT_DIR, "daily_demand.csv")

        raw_df.to_csv(raw_path, index=False)
        daily_df.to_csv(daily_path, index=False)

        print(f"✅ {len(raw_df)} lignes exportées vers {raw_path}")
        print(f"✅ {len(daily_df)} lignes exportées vers {daily_path}")
        print("\nAperçu du dataset agrégé (daily_demand.csv) :")
        print(daily_df.head(10))
    finally:
        db.close()


if __name__ == "__main__":
    main()