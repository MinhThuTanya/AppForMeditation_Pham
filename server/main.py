"""Akii Server — сервер для необязательного аккаунта и синхронизации.
Запуск из папки проекта:  uvicorn server.main:app --reload
Документация API откроется по адресу http://127.0.0.1:8000/docs"""
from fastapi import FastAPI
from sqlalchemy import event

from server import auth, sync
from server.models import Base, engine

app = FastAPI(title="Akii Server", version="1.0")
app.include_router(auth.router)
app.include_router(sync.router)

if engine.url.get_backend_name() == "sqlite":
    @event.listens_for(engine, "connect")
    def _fk_on(conn, _):
        conn.execute("PRAGMA foreign_keys = ON")

Base.metadata.create_all(engine)


@app.get("/")
def health():
    return {"service": "Akii Server", "status": "ok"}
