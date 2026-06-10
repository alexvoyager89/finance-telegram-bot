"""Обработчики команд: /start, /income, /expense, /balance, /stats, /undo."""

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import DEFAULT_CATEGORY
from bot.handlers.common import clear_pending_state
from bot.handlers.decorators import log_handler
from bot.logger import log_action
from bot.keyboards import main_keyboard
from bot.messages import (
    fmt_balance_message,
    fmt_hint,
    fmt_start_message,
    fmt_stats_message,
    fmt_transaction_message,
    fmt_undo_empty,
    fmt_undo_success,
    format_amount_error,
)
from bot.parsers import parse_amount
from bot.storage import (
    read_balance,
    read_stats,
    record_expense_cat,
    record_income_cat,
    undo_last_operation,
)


@log_handler("command:/start")
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None:
        return
    clear_pending_state(context)
    await update.message.reply_text(
        fmt_start_message(),
        reply_markup=main_keyboard(),
        parse_mode="HTML",
    )


@log_handler("command:/income")
async def income(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None:
        return
    user_id = update.effective_user.id

    if not context.args:
        log_action(update, "income_invalid", "нет аргументов")
        await update.message.reply_text(
            fmt_hint("Пример: <code>/income 1000 зарплата</code>"),
            parse_mode="HTML",
        )
        return

    amount, err = parse_amount([context.args[0]])
    if err:
        log_action(update, "income_invalid", f"ошибка ввода: {err}")
        if err == "missing":
            await update.message.reply_text(
                fmt_hint("Укажи сумму: <code>/income 1000</code>"),
                parse_mode="HTML",
            )
        else:
            await update.message.reply_text(
                format_amount_error(err), parse_mode="HTML"
            )
        return

    category = (
        " ".join(context.args[1:]).strip()
        if len(context.args) > 1
        else DEFAULT_CATEGORY
    )
    balance = record_income_cat(user_id, amount, category)
    log_action(
        update,
        "income_added",
        f"amount={amount} category={category} balance={balance}",
    )
    await update.message.reply_text(
        fmt_transaction_message("income", amount, category, balance),
        parse_mode="HTML",
    )


@log_handler("command:/expense")
async def expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None:
        return
    user_id = update.effective_user.id

    if not context.args:
        log_action(update, "expense_invalid", "нет аргументов")
        await update.message.reply_text(
            fmt_hint("Пример: <code>/expense 200 еда</code>"),
            parse_mode="HTML",
        )
        return

    amount, err = parse_amount([context.args[0]])
    if err:
        log_action(update, "expense_invalid", f"ошибка ввода: {err}")
        if err == "missing":
            await update.message.reply_text(
                fmt_hint("Укажи сумму: <code>/expense 200</code>"),
                parse_mode="HTML",
            )
        else:
            await update.message.reply_text(
                format_amount_error(err), parse_mode="HTML"
            )
        return

    category = (
        " ".join(context.args[1:]).strip()
        if len(context.args) > 1
        else DEFAULT_CATEGORY
    )
    balance = record_expense_cat(user_id, amount, category)
    log_action(
        update,
        "expense_added",
        f"amount={amount} category={category} balance={balance}",
    )
    await update.message.reply_text(
        fmt_transaction_message("expense", amount, category, balance),
        parse_mode="HTML",
    )


@log_handler("command:/balance")
async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None:
        return
    balance = read_balance(update.effective_user.id)
    await update.message.reply_text(
        fmt_balance_message(balance),
        parse_mode="HTML",
    )


@log_handler("command:/stats")
async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None:
        return
    stats = read_stats(update.effective_user.id)
    await update.message.reply_text(
        fmt_stats_message(stats),
        parse_mode="HTML",
    )


@log_handler("command:/undo")
async def undo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None:
        return
    ok, operation, balance = undo_last_operation(update.effective_user.id)
    if not ok or operation is None:
        log_action(update, "undo_empty", "нечего отменять")
        await update.message.reply_text(fmt_undo_empty(), parse_mode="HTML")
        return
    log_action(
        update,
        "undo_ok",
        f"kind={operation.get('kind')} amount={operation.get('amount')} "
        f"category={operation.get('category')} balance={balance}",
    )
    await update.message.reply_text(
        fmt_undo_success(operation, balance),
        parse_mode="HTML",
    )
