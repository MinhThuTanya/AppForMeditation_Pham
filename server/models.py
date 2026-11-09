"""Таблицы сервера Akii Server (PostgreSQL; для разработки — SQLite)."""
import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, String, Text,
                        UniqueConstraint, create_engine)
from sqlalchemy.orm import declarative_base, sessionmaker

# Пример для PostgreSQL: postgresql+psycopg://akii:пароль@localhost:5432/akii
DATABASE_URL = os.environ.get("AKII_DATABASE_URL", "sqlite:///./akii_server.db")

engine = create_engine(DATABASE_URL, future=True,
                       connect_args={"check_same_thread": False}
                       if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)
Base = declarative_base()


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def new_id():
    return uuid.uuid4().hex


class User(Base):
    """Аккаунт: почта, хеш пароля (Argon2), имя, дата регистрации."""
    __tablename__ = "users"
    id = Column(String(32), primary_key=True, default=new_id)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255))
    display_name = Column(String(100))
    email_confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)


class Identity(Base):
    """Привязанный способ входа: google, vk, apple."""
    __tablename__ = "identities"
    id = Column(String(32), primary_key=True, default=new_id)
    user_id = Column(String(32), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider = Column(String(20), nullable=False)
    provider_user_id = Column(String(255), nullable=False)
    __table_args__ = (UniqueConstraint("provider", "provider_user_id"),)


class Token(Base):
    """Токены: доступа (access) и подтверждения почты (confirm)."""
    __tablename__ = "tokens"
    token = Column(String(64), primary_key=True)
    user_id = Column(String(32), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind = Column(String(10), default="access")
    expires_at = Column(DateTime, nullable=False)


class Record(Base):
    """Резервная копия записи пользователя (одна строка локальной таблицы)."""
    __tablename__ = "records"
    id = Column(String(32), primary_key=True, default=new_id)
    user_id = Column(String(32), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    table_name = Column(String(30), nullable=False)
    record_key = Column(String(255), nullable=False)
    payload = Column(Text, nullable=False)          # JSON
    updated_at = Column(String(32), nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "table_name", "record_key"),)


class Subscription(Base):
    """Статус Akii Plus, если подписка оформлена после входа."""
    __tablename__ = "subscriptions"
    user_id = Column(String(32), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    plan = Column(String(30))
    status = Column(String(10), default="inactive")
    expires_at = Column(String(10))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
