"""Сборка и запуск Telegram-приложения."""

from telegram import BotCommand, Update
from telegram.error import InvalidToken
from telegram.ext import Application, ApplicationBuilder, ContextTypes

from bot.config import load_token
from bot.handlers import register_handlers
from bot.logger import log_action, log_error, setup_logging


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Глобальный обработчик ошибок python-telegram-bot."""
    tg_update = update if isinstance(update, Update) else None
    log_error(
        tg_update,
        "Необработанная ошибка в приложении",
        context.error if isinstance(context.error, BaseException) else None,
    )


async def post_init(application: Application) -> None:
    """Команды в меню Telegram (кнопка «/» в поле ввода)."""
    await application.bot.set_my_commands(
        [
            BotCommand("start", "Меню и клавиатура"),
            BotCommand("balance", "Мой баланс"),
            BotCommand("income", "Доход — /income 1000 зарплата"),
            BotCommand("expense", "Расход — /expense 200 еда"),
            BotCommand("stats", "Статистика доходов и расходов"),
            BotCommand("undo", "Отменить последнюю операцию"),
        ]
    )


def main() -> None:
    setup_logging()
    log_action(None, "bot_start", "запуск приложения")

    bot_token = load_token()
    if not bot_token:
        log_error(None, "Токен не найден: проверь файл .env")
        print("Ошибка: не найден токен бота.")
        print("Создай файл .env в папке проекта и добавь строку:")
        print("TELEGRAM_BOT_TOKEN=твой_токен_от_BotFather")
        print("(можно скопировать шаблон: copy .env.example .env)")
        return

    app = (
        ApplicationBuilder()
        .token(bot_token)
        .post_init(post_init)
        .build()
    )
    app.add_error_handler(on_error)
    register_handlers(app)

    log_action(None, "bot_polling", "бот слушает сообщения")
    print("Бот запущен...")
    try:
        app.run_polling()
    except InvalidToken as exc:
        log_error(None, "Telegram отклонил токен", exc)
        print("Ошибка: Telegram отклонил токен. Проверь токен из @BotFather.")
    except Exception as exc:
        log_error(None, "Критическая ошибка при работе бота", exc)
        raise
