"""Регистрация по почте, вход по паролю и через Google / VK ID / Apple (OAuth 2.0)."""
import json
import os
import secrets
import smtplib
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from email.message import EmailMessage

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from server.models import Identity, Token, User, get_db, utcnow

router = APIRouter(prefix="/auth", tags=["auth"])
hasher = PasswordHasher()                     # Argon2id
PUBLIC_URL = os.environ.get("AKII_PUBLIC_URL", "http://127.0.0.1:8000")
ACCESS_DAYS = 30

# Данные приложения из кабинетов разработчика (заполняются на этапе 9.4)
OAUTH = {
    "google": {"token_url": "https://oauth2.googleapis.com/token",
               "userinfo_url": "https://openidconnect.googleapis.com/v1/userinfo",
               "client_id": os.environ.get("GOOGLE_CLIENT_ID", "")},
    "vk": {"token_url": "https://id.vk.com/oauth2/auth",
           "userinfo_url": "https://id.vk.com/oauth2/user_info",
           "client_id": os.environ.get("VK_CLIENT_ID", "")},
    "apple": {"token_url": "https://appleid.apple.com/auth/token",
              "client_id": os.environ.get("APPLE_CLIENT_ID", "")},
}


class RegisterIn(BaseModel):
    email: str
    password: str
    display_name: str = ""


class LoginIn(BaseModel):
    email: str
    password: str


class OAuthIn(BaseModel):
    code: str
    code_verifier: str
    redirect_uri: str
    device_id: str | None = None    # VK ID передаёт его вместе с кодом


def issue_token(db, user_id, kind="access", days=ACCESS_DAYS):
    token = secrets.token_urlsafe(32)
    db.add(Token(token=token, user_id=user_id, kind=kind,
                 expires_at=utcnow() + timedelta(days=days)))
    db.commit()
    return token


def current_user(authorization: str = Header(default=""), db: Session = Depends(get_db)):
    """Зависимость: пользователь по заголовку Authorization: Bearer <токен>."""
    token = authorization.removeprefix("Bearer ").strip()
    row = db.get(Token, token) if token else None
    if not row or row.kind != "access" or row.expires_at < utcnow():
        raise HTTPException(401, "not_signed_in")
    return db.get(User, row.user_id)


def send_confirmation(email, link):
    """Письмо для подтверждения почты. Без настроек SMTP ссылка выводится в консоль."""
    host = os.environ.get("AKII_SMTP_HOST")
    if not host:
        print(f"[Akii] Подтверждение почты {email}: {link}")
        return
    msg = EmailMessage()
    msg["Subject"] = "Akii: подтвердите почту / confirm your email"
    msg["From"] = os.environ.get("AKII_SMTP_FROM", "no-reply@akii.app")
    msg["To"] = email
    msg.set_content(f"Чтобы подтвердить почту, откройте ссылку:\n{link}")
    with smtplib.SMTP_SSL(host, int(os.environ.get("AKII_SMTP_PORT", 465))) as s:
        s.login(os.environ["AKII_SMTP_USER"], os.environ["AKII_SMTP_PASSWORD"])
        s.send_message(msg)


def account_answer(db, user, provider):
    return {"access_token": issue_token(db, user.id), "user_id": user.id,
            "email": user.email, "display_name": user.display_name, "provider": provider}


@router.post("/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    email = data.email.strip().lower()
    if "@" not in email or len(data.password) < 8:
        raise HTTPException(400, "Проверьте почту и пароль (не короче 8 символов)")
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(409, "Аккаунт с этой почтой уже есть")
    user = User(email=email, password_hash=hasher.hash(data.password),
                display_name=data.display_name or email.split("@")[0])
    db.add(user)
    db.commit()
    token = issue_token(db, user.id, kind="confirm", days=2)
    send_confirmation(email, f"{PUBLIC_URL}/auth/confirm?token={token}")
    return {"status": "check_email"}


@router.get("/confirm")
def confirm(token: str, db: Session = Depends(get_db)):
    row = db.get(Token, token)
    if not row or row.kind != "confirm" or row.expires_at < utcnow():
        raise HTTPException(400, "Ссылка устарела")
    user = db.get(User, row.user_id)
    user.email_confirmed = True
    db.delete(row)
    db.commit()
    return {"status": "confirmed", "message": "Почта подтверждена. Вернитесь в приложение Akii и войдите."}


@router.post("/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=data.email.strip().lower()).first()
    try:
        ok = bool(user and user.password_hash and hasher.verify(user.password_hash, data.password))
    except VerifyMismatchError:
        ok = False
    if not ok:
        raise HTTPException(401, "Неверная почта или пароль")
    if not user.email_confirmed:
        raise HTTPException(403, "Сначала подтвердите почту по ссылке из письма")
    return account_answer(db, user, "email")


def _post_form(url, fields):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(fields).encode(), method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def fetch_profile(provider, data: OAuthIn):
    """Обмен кода авторизации на токен и получение id и почты пользователя."""
    cfg = OAUTH[provider]
    if not cfg["client_id"]:
        raise HTTPException(501, "Вход через этот сервис ещё не настроен на сервере")
    fields = {"grant_type": "authorization_code", "code": data.code,
              "code_verifier": data.code_verifier, "redirect_uri": data.redirect_uri,
              "client_id": cfg["client_id"]}
    if provider == "vk":
        fields["device_id"] = data.device_id or ""
    if provider == "google":
        fields["client_secret"] = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    if provider == "apple":
        # Apple требует client_secret в виде JWT, подписанного ключом из Apple Developer
        raise HTTPException(501, "Вход через Apple настраивается при публикации в App Store")
    tok = _post_form(cfg["token_url"], fields)
    if provider == "vk":
        info = _post_form(cfg["userinfo_url"], {"access_token": tok["access_token"],
                                                "client_id": cfg["client_id"]})["user"]
        return str(info["user_id"]), info.get("email"), info.get("first_name")
    req = urllib.request.Request(cfg["userinfo_url"],
                                 headers={"Authorization": "Bearer " + tok["access_token"]})
    with urllib.request.urlopen(req, timeout=10) as r:
        info = json.loads(r.read())
    return info["sub"], info.get("email"), info.get("given_name")


@router.post("/oauth/{provider}")
def oauth(provider: str, data: OAuthIn, db: Session = Depends(get_db)):
    if provider not in OAUTH:
        raise HTTPException(404, "Неизвестный способ входа")
    pid, email, name = fetch_profile(provider, data)
    return link_identity(db, provider, pid, email, name)


def link_identity(db, provider, pid, email, name):
    """Находит или создаёт аккаунт. Входы с одной подтверждённой почтой
    объединяются в один аккаунт (подраздел 2.8 курсовой)."""
    ident = db.query(Identity).filter_by(provider=provider, provider_user_id=pid).first()
    if ident:
        user = db.get(User, ident.user_id)
    else:
        user = db.query(User).filter_by(email=email.lower()).first() if email else None
        if not user:
            user = User(email=email.lower() if email else None, display_name=name,
                        email_confirmed=bool(email))
            db.add(user)
            db.commit()
        db.add(Identity(user_id=user.id, provider=provider, provider_user_id=pid))
        db.commit()
    return account_answer(db, user, provider)
