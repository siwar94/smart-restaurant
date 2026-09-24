from fastapi import FastAPI
from sqlalchemy import text

from app.database.session import engine
from app import models  # <-- ajouté pour valider les modèles

app = FastAPI(title="Smart Restaurant Order System API")


@app.get("/")
def root():
    return {"message": "Smart Restaurant API is running"}


@app.get("/health/db")
def health_db():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"database": "connected"}
    except Exception as e:
        return {"database": "error", "detail": str(e)}