"""Общие вспомогательные функции для обработчиков."""

from telegram.ext import ContextTypes


def clear_pending_state(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Сбрасывает ожидание ввода суммы или категории."""
    context.user_data.pop("pending", None)
    context.user_data.pop("pending_category", None)
    context.user_data.pop("pending_kind", None)
