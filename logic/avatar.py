from logic.database import (get_streak, get_days_without_practice,
                            get_last_mood, get_connection, DB_PATH)

SPRITES = {
    "glowing": "assets/images/avatar/glowing.png",
    "sad": "assets/images/avatar/sad.png",
    "anxious": "assets/images/avatar/anxious.png",
    "tired": "assets/images/avatar/tired.png",
    "calm": "assets/images/avatar/calm.png",
}


def choose_state(streak, days_without, last_mood):
    """Правила выбора состояния Аватара (проверяются по приоритету)."""
    if streak >= 7:
        return "glowing"
    if days_without is not None and days_without >= 3:
        return "sad"
    if last_mood == "тревога":
        return "anxious"
    if last_mood == "усталость":
        return "tired"
    return "calm"


def update_avatar(path=DB_PATH):
    state = choose_state(get_streak(path),
                         get_days_without_practice(path),
                         get_last_mood(path))
    with get_connection(path) as conn:
        conn.execute("UPDATE settings SET avatar_state = ? WHERE id = 1",
                     (state,))
    return state, SPRITES[state]
