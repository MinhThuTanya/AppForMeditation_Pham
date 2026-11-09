from datetime import datetime, date
from logic.database import get_connection, DB_PATH

PRODUCTS = {"akii_plus_month": 30, "akii_plus_year": 365}


def is_premium(path=DB_PATH, today=None):
    """Проверка подписки Akii Plus по локальной записи (работает офлайн)."""
    today = today or date.today().isoformat()
    with get_connection(path) as conn:
        row = conn.execute(
            "SELECT status, expires_at FROM subscription WHERE id = 1"
        ).fetchone()
    return bool(row and row[0] == "active" and row[1] and row[1] >= today)


def activate(product_id, purchase_id, expires_at, path=DB_PATH):
    """Сохраняет результат успешной покупки, полученный от RuStore Pay SDK."""
    if product_id not in PRODUCTS:
        raise ValueError("Неизвестный тариф")
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection(path) as conn:
        conn.execute(
            "UPDATE subscription SET plan = ?, status = 'active',"
            " purchase_id = ?, expires_at = ?, last_checked = ? WHERE id = 1",
            (product_id, purchase_id, expires_at, now))


def deactivate(path=DB_PATH):
    """Вызывается, если при проверке выяснилось, что подписка закончилась.
    Записи пользователя при этом не затрагиваются."""
    with get_connection(path) as conn:
        conn.execute("UPDATE subscription SET status = 'inactive' WHERE id = 1")


# ---- Выбор платёжной системы по платформе ----

def get_store(platform):
    """android → RuStore Pay SDK, ios → StoreKit, иначе тестовый режим
    (запуск на компьютере во время разработки)."""
    return {"android": "rustore", "ios": "appstore"}.get(platform, "test")


def purchase(product_id, platform, path=DB_PATH, today=None):
    """Оформление подписки. На компьютере работает тестовый режим без
    оплаты: подписка просто активируется на срок тарифа."""
    store = get_store(platform)
    if store == "test":
        from datetime import timedelta
        today = today or date.today()
        expires = (today + timedelta(days=PRODUCTS[product_id])).isoformat()
        activate(product_id, "TEST-" + today.strftime("%Y%m%d"), expires, path)
        return True
    # Интеграция с RuStore Pay SDK (Pyjnius) и StoreKit (Pyobjus) —
    # этап 9.3 плана разработки, проверяется на устройстве.
    raise NotImplementedError(f"Оплата через {store} подключается на этапе 9.3")


def restore(platform, path=DB_PATH):
    """Восстановление покупки. В тестовом режиме — проверка локальной записи."""
    if get_store(platform) == "test":
        return is_premium(path)
    raise NotImplementedError("Восстановление покупки подключается на этапе 9.3")


def get_subscription(path=DB_PATH):
    with get_connection(path) as conn:
        return conn.execute(
            "SELECT plan, status, expires_at FROM subscription WHERE id = 1"
        ).fetchone()
