"""Настройка логов: действия пользователей и ошибки."""

import logging
from logging.handlers import RotatingFileHandler

from telegram import Update

from bot.config import LOG_DIR

_actions_logger: logging.Logger | None = None
_errors_logger: logging.Logger | None = None


def setup_logging() -> None:
    """Включает запись логов в файл logs/bot.log и в консоль."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / "bot.log"

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger("bot")
    root.setLevel(logging.INFO)
    root.handlers.clear()

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root.addHandler(file_handler)
    root.addHandler(console_handler)

    global _actions_logger, _errors_logger
    _actions_logger = logging.getLogger("bot.actions")
    _errors_logger = logging.getLogger("bot.errors")

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)

    _actions_logger.info("Логирование запущено. Файл: %s", log_file)


def _user_prefix(update: Update | None) -> str:
    if update is None or update.effective_user is None:
        return "user_id=? username=-"
    user = update.effective_user
    username = f"@{user.username}" if user.username else "-"
    return f"user_id={user.id} username={username}"


def log_action(update: Update | None, action: str, details: str = "") -> None:
    """Записывает действие пользователя (команда, кнопка, операция)."""
    logger = _actions_logger or logging.getLogger("bot.actions")
    message = f"{_user_prefix(update)} | action={action}"
    if details:
        message += f" | {details}"
    logger.info(message)


def log_error(
    update: Update | None,
    message: str,
    exc: BaseException | None = None,
) -> None:
    """Записывает ошибку (с traceback, если передано исключение)."""
    logger = _errors_logger or logging.getLogger("bot.errors")
    text = f"{_user_prefix(update)} | {message}"
    if exc is not None:
        logger.error(text, exc_info=exc)
    else:
        logger.error(text)
