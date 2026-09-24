from fastapi import FastAPI
from sqlalchemy import text

from app.database.session import engine
from app import models
from app.routers import auth, users, tables

app = FastAPI(title="Smart Restaurant Order System API")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tables.router)


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