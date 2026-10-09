import os
from datetime import date
from functools import lru_cache

import joblib
import pandas as pd
from sqlalchemy.orm import Session

from app.models.menu_item import MenuItem

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "models", "demand_model.joblib")


class ModelNotAvailableError(Exception):
    """Levée quand aucun modèle entraîné n'est disponible sur disque."""


@lru_cache(maxsize=1)
def _load_model_bundle():
    """Charge le modèle une seule fois (mis en cache en mémoire pour les appels suivants)."""
    if not os.path.exists(MODEL_PATH):
        raise ModelNotAvailableError(
            "Aucun modèle entraîné trouvé. Lance scripts/train_demand_model.py."
        )
    return joblib.load(MODEL_PATH)


def predict_demand(db: Session, target_date: date) -> list[dict]:
    """Prédit, pour chaque plat disponible, la quantité qui devrait être vendue
    le `target_date` donné, en se basant sur le jour de la semaine."""
    bundle = _load_model_bundle()
    model = bundle["model"]
    feature_columns = bundle["feature_columns"]
    trained_item_ids = {
        int(col.replace("item_", ""))
        for col in feature_columns
        if col.startswith("item_")
    }

    day_of_week = target_date.weekday()  # 0=lundi ... 6=dimanche
    menu_items = db.query(MenuItem).filter(MenuItem.available == True).all()

    predictions = []
    for item in menu_items:
        if item.id not in trained_item_ids:
            # Plat ajouté après l'entraînement : pas encore d'historique pour lui,
            # on l'ignore plutôt que de renvoyer une prédiction non fiable.
            continue

        row = {col: 0 for col in feature_columns}
        row[f"item_{item.id}"] = 1
        dow_col = f"dow_{day_of_week}"
        if dow_col in row:
            row[dow_col] = 1

        X = pd.DataFrame([row], columns=feature_columns)
        predicted_qty = max(0, round(float(model.predict(X)[0])))

        predictions.append(
            {
                "menu_item_id": item.id,
                "menu_item_name": item.name,
                "predicted_quantity": predicted_qty,
            }
        )

    predictions.sort(key=lambda p: p["predicted_quantity"], reverse=True)
    return predictions