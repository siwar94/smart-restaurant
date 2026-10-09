"""Génère des règles d'association 'plats souvent commandés ensemble' à partir
de l'historique des commandes (market basket analysis simplifié aux paires).
Usage : python -m scripts.train_recommendations
"""
import os
from collections import defaultdict
from itertools import combinations

import joblib

from app.database.session import SessionLocal
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.menu_item import MenuItem

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
MIN_SUPPORT = 0.02
MIN_CONFIDENCE = 0.25
TOP_N_PER_ITEM = 3


def get_order_item_sets(db):
    """Retourne {order_id: {menu_item_id, ...}} pour toutes les commandes SERVED."""
    rows = (
        db.query(OrderItem.order_id, OrderItem.menu_item_id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.status == OrderStatus.SERVED)
        .all()
    )
    order_items = defaultdict(set)
    for order_id, menu_item_id in rows:
        order_items[order_id].add(menu_item_id)
    return order_items


def compute_association_rules(order_items: dict) -> list:
    total_orders = len(order_items)
    item_count = defaultdict(int)
    pair_count = defaultdict(int)

    for items in order_items.values():
        for item in items:
            item_count[item] += 1
        for a, b in combinations(sorted(items), 2):
            pair_count[(a, b)] += 1

    # Règles dans les deux sens (A->B et B->A) : confiance et lift ne sont pas symétriques.
    raw_rules = []
    for (a, b), count in pair_count.items():
        support = count / total_orders
        if support < MIN_SUPPORT:
            continue

        conf_a_to_b = count / item_count[a]
        conf_b_to_a = count / item_count[b]
        lift = count * total_orders / (item_count[a] * item_count[b])

        if conf_a_to_b >= MIN_CONFIDENCE:
            raw_rules.append((a, b, conf_a_to_b, lift, support))
        if conf_b_to_a >= MIN_CONFIDENCE:
            raw_rules.append((b, a, conf_b_to_a, lift, support))

    return raw_rules


def build_recommendations(db, raw_rules: list) -> dict:
    menu_items = {m.id: m.name for m in db.query(MenuItem).all()}

    by_source = defaultdict(list)
    for source, target, confidence, lift, support in raw_rules:
        by_source[source].append(
            {
                "menu_item_id": target,
                "menu_item_name": menu_items.get(target, "?"),
                "confidence": round(confidence, 3),
                "lift": round(lift, 2),
                "support": round(support, 3),
            }
        )

    recommendations = {}
    for source, targets in by_source.items():
        targets.sort(key=lambda r: r["lift"], reverse=True)
        recommendations[source] = targets[:TOP_N_PER_ITEM]

    return recommendations


def main():
    db = SessionLocal()
    try:
        order_items = get_order_item_sets(db)
        if len(order_items) < 30:
            print(
                "⚠️  Pas assez de commandes pour des règles fiables. "
                "Lance scripts/seed_historical_orders.py si besoin."
            )
            return

        raw_rules = compute_association_rules(order_items)
        recommendations = build_recommendations(db, raw_rules)

        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump(recommendations, os.path.join(MODEL_DIR, "recommendations.joblib"))

        print(f"✅ {len(recommendations)} plats ont au moins une recommandation associée.")
        print(f"✅ Sauvegardé dans {MODEL_DIR}/recommendations.joblib\n")

        print("Aperçu :")
        for source_id, targets in list(recommendations.items())[:5]:
            source_name = db.get(MenuItem, source_id).name
            for t in targets:
                print(
                    f"  {source_name} → {t['menu_item_name']} "
                    f"(confiance={t['confidence']}, lift={t['lift']})"
                )
    finally:
        db.close()


if __name__ == "__main__":
    main()