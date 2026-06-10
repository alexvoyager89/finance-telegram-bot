"""Настройки бота: пути к файлам, категории, подписи кнопок."""

import os
from pathlib import Path

# Корень проекта (папка, где лежит telegram_bot.py)
PROJECT_DIR = Path(__file__).resolve().parent.parent

DATA_FILE = PROJECT_DIR / "telegram_bot_balance.json"
LOG_DIR = PROJECT_DIR / "logs"

# Секретный файл с токеном (не публикуй его и не отправляй в git)
ENV_FILE = PROJECT_DIR / ".env"
ENV_TOKEN_KEY = "TELEGRAM_BOT_TOKEN"

DEFAULT_CATEGORY = "без категории"

# Подписи кнопок клавиатуры
BTN_START = "/start"
BTN_BALANCE = "💰 Баланс"
BTN_STATS = "📊 Статистика"
BTN_INCOME = "➕ Доход"
BTN_EXPENSE = "➖ Расход"
BTN_UNDO = "↩️ Отменить последнюю"
BTN_BACK = "⬅️ Назад"

# Списки категорий (можно менять под себя)
EXPENSE_CATEGORIES: list[str] = [
    "аренда",
    "коммунальные услуги",
    "еда",
    "транспорт",
    "развлечения",
    "долг",
    "здоровье",
    "покупки",
    "подписки",
    "подарки",
    "прочее",
]

INCOME_CATEGORIES: list[str] = [
    "зарплата",
    "долг",
    "подарки",
    "подработка",
    "инвестиции",
    "прочее",
]


def load_token() -> str:
    """
    Загружает токен бота из .env (или из переменной окружения).

    Порядок поиска:
    1) переменная окружения TELEGRAM_BOT_TOKEN (если задана в системе)
    2) строка TELEGRAM_BOT_TOKEN=... в файле .env рядом с telegram_bot.py
    """
    token = os.getenv(ENV_TOKEN_KEY, "").strip()
    if token:
        return token

    if not ENV_FILE.exists():
        return ""

    with open(ENV_FILE, "r", encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith(f"{ENV_TOKEN_KEY}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")

    return ""
