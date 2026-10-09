import os
from functools import lru_cache

import joblib
from sqlalchemy.orm import Session

from app.models.menu_item import MenuItem

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "models", "recommendations.joblib")


class ModelNotAvailableError(Exception):
    """Levée quand aucune règle de recommandation n'est disponible sur disque."""


@lru_cache(maxsize=1)
def _load_recommendations() -> dict:
    if not os.path.exists(MODEL_PATH):
        raise ModelNotAvailableError(
            "Aucune règle de recommandation trouvée. Lance scripts/train_recommendations.py."
        )
    return joblib.load(MODEL_PATH)


def get_recommendations_for_item(menu_item_id: int) -> list[dict]:
    recommendations = _load_recommendations()
    return recommendations.get(menu_item_id, [])


def get_all_recommendations(db: Session) -> list[dict]:
    recommendations = _load_recommendations()
    menu_items = {m.id: m.name for m in db.query(MenuItem).all()}

    result = []
    for source_id, targets in recommendations.items():
        if source_id not in menu_items:
            continue
        result.append(
            {
                "menu_item_id": source_id,
                "menu_item_name": menu_items[source_id],
                "recommendations": targets,
            }
        )
    result.sort(key=lambda r: r["menu_item_name"])
    return result