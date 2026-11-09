import json
from datetime import date
from logic.database import get_connection, DB_PATH

# (текст вопроса, прямой ли вопрос: True — высокий балл = больше стресса)
QUESTIONS = [
    ("Как вы оцениваете свой уровень стресса?", True),
    ("Как вы спали последнюю ночь?", False),
    ("Какой у вас уровень энергии?", False),
    ("Часто ли вы чувствуете тревогу?", True),
    ("Насколько легко вы расслабляетесь?", False),
]


def calculate_stress(answers):
    """Возвращает интегральный индекс стресса S и его категорию."""
    if len(answers) != len(QUESTIONS):
        raise ValueError("Нужно ответить на все вопросы")
    scores = []
    for x, (_, direct) in zip(answers, QUESTIONS):
        if not 1 <= x <= 10:
            raise ValueError("Ответ должен быть в диапазоне 1..10")
        scores.append(x if direct else 11 - x)
    s = round(sum(scores) / len(scores), 1)
    if s < 4:
        category = "низкий"
    elif s <= 7:
        category = "умеренный"
    else:
        category = "высокий"
    return s, category


def save_stress_result(answers, path=DB_PATH):
    s, category = calculate_stress(answers)
    with get_connection(path) as conn:
        conn.execute(
            "INSERT INTO stress_tests (date, answers, score, category)"
            " VALUES (?, ?, ?, ?)",
            (date.today().isoformat(), json.dumps(answers), s, category))
    return s, category
