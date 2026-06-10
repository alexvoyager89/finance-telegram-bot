"""Декораторы для логирования обработчиков."""

import functools
from collections.abc import Callable
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

from bot.logger import log_action, log_error


def log_handler(action_name: str) -> Callable:
    """Логирует вход в обработчик и перехватывает необработанные ошибки."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(
            update: Update, context: ContextTypes.DEFAULT_TYPE
        ) -> Any:
            log_action(update, action_name)
            try:
                return await func(update, context)
            except Exception as exc:
                log_error(update, f"Ошибка в обработчике '{action_name}'", exc)
                if update.message:
                    await update.message.reply_text(
                        "⚠️ Произошла ошибка. Попробуй ещё раз или нажми /start."
                    )
                return None

        return wrapper

    return decorator
