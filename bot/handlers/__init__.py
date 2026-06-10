"""Регистрация всех обработчиков сообщений бота."""

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from bot.handlers.commands import (
    balance_cmd,
    expense,
    income,
    start,
    stats_cmd,
    undo_cmd,
)
from bot.handlers.text import on_text


def register_handlers(app: Application) -> None:
    """Подключает команды и обработчик текста к приложению."""
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("income", income))
    app.add_handler(CommandHandler("expense", expense))
    app.add_handler(CommandHandler("balance", balance_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("undo", undo_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
