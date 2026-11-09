"""Синхронизация данных и удаление аккаунта."""
import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from server.auth import current_user
from server.models import Record, User, get_db

router = APIRouter(tags=["sync"])

# Как отличать записи одной таблицы друг от друга
KEYS = {
    "journal_entries": lambda r: r["entry_date"],
    "moods": lambda r: f'{r["date"]}|{r["mood"]}|{r.get("note") or ""}',
    "sessions": lambda r: f'{r["date"]}|{r["duration"]}|{r.get("meditation_type") or ""}|{r.get("id")}',
    "dreams": lambda r: f'{r["date"]}|{r.get("tags") or ""}',
    "stress_tests": lambda r: f'{r["date"]}|{r["score"]}',
}


class SyncIn(BaseModel):
    changes: dict[str, list[dict]] = {}


@router.post("/sync")
def sync(data: SyncIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Принимает изменённые записи и возвращает все записи пользователя.
    При конфликте сохраняется более поздняя версия (по updated_at или дате)."""
    for table, rows in data.changes.items():
        if table not in KEYS:
            continue
        for row in rows:
            key = KEYS[table](row)
            stamp = str(row.get("updated_at") or row.get("date") or "")
            rec = db.query(Record).filter_by(user_id=user.id, table_name=table,
                                             record_key=key).first()
            if rec is None:
                db.add(Record(user_id=user.id, table_name=table, record_key=key,
                              payload=json.dumps(row, ensure_ascii=False), updated_at=stamp))
            elif stamp >= rec.updated_at:
                rec.payload = json.dumps(row, ensure_ascii=False)
                rec.updated_at = stamp
    db.commit()
    result = {}
    for rec in db.query(Record).filter_by(user_id=user.id):
        result.setdefault(rec.table_name, []).append(json.loads(rec.payload))
    return {"changes": result}


@router.delete("/account")
def delete_account(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Удаляет аккаунт и все данные пользователя на сервере (право отозвать согласие, 152-ФЗ)."""
    db.delete(user)
    db.commit()
    return {"status": "deleted"}
