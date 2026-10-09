"""Entraîne un modèle de prévision de la demande (quantité vendue par plat et par jour).
Usage : python scripts/train_demand_model.py
"""
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "daily_demand.csv")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")


def load_dataset() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def build_features(df: pd.DataFrame):
    """Transforme le dataset en matrice de features exploitable par le modèle.
    menu_item_id et day_of_week sont catégoriels -> one-hot encoding (un modèle
    d'arbres n'a pas besoin de normalisation, mais l'encodage catégoriel évite
    de laisser croire à une relation d'ordre entre des IDs arbitraires)."""
    item_dummies = pd.get_dummies(df["menu_item_id"], prefix="item")
    dow_dummies = pd.get_dummies(df["day_of_week"], prefix="dow")
    X = pd.concat([item_dummies, dow_dummies], axis=1)
    y = df["total_quantity"]
    return X, y


def time_based_split(df: pd.DataFrame, X: pd.DataFrame, y: pd.Series, test_ratio: float = 0.15):
    """Split chronologique (pas aléatoire) : les derniers jours servent de test.
    C'est la bonne pratique pour une série temporelle — un split aléatoire
    laisserait le modèle s'entraîner sur des jours proches du test (fuite
    d'information), ce qui fausserait artificiellement l'évaluation."""
    threshold_date = df["date"].quantile(1 - test_ratio, interpolation="nearest")
    train_mask = df["date"] < threshold_date
    test_mask = ~train_mask
    return X[train_mask], X[test_mask], y[train_mask], y[test_mask]


def evaluate(y_true, y_pred, label: str):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    print(f"{label:20s} — MAE: {mae:.2f} | RMSE: {rmse:.2f} | R²: {r2:.3f}")
    return mae, rmse, r2


def main():
    df = load_dataset()
    if len(df) < 50:
        print(
            "⚠️  Dataset trop petit pour un entraînement fiable. "
            "Relance scripts/seed_historical_orders.py puis scripts/export_dataset.py."
        )
        return

    X, y = build_features(df)
    X_train, X_test, y_train, y_test = time_based_split(df, X, y)

    print(f"Entraînement sur {len(X_train)} exemples, test sur {len(X_test)} exemples "
          f"(coupure chronologique).\n")

    # --- Baseline naïve : moyenne historique par plat, pour donner un point de repère ---
    train_df = df.loc[X_train.index]
    item_means = train_df.groupby("menu_item_id")["total_quantity"].mean()
    baseline_pred = df.loc[X_test.index, "menu_item_id"].map(item_means).fillna(y_train.mean())
    evaluate(y_test, baseline_pred, "Baseline (moyenne)")

    # --- Modèle Random Forest ---
    model = RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    evaluate(y_test, y_pred, "RandomForest")

    # --- Sauvegarde du modèle + métadonnées nécessaires à la prédiction ---
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "feature_columns": list(X.columns),
            "menu_item_names": (
                df[["menu_item_id", "menu_item_name"]]
                .drop_duplicates()
                .set_index("menu_item_id")["menu_item_name"]
                .to_dict()
            ),
        },
        os.path.join(MODEL_DIR, "demand_model.joblib"),
    )
    print(f"\n✅ Modèle sauvegardé dans {MODEL_DIR}/demand_model.joblib")


if __name__ == "__main__":
    main()